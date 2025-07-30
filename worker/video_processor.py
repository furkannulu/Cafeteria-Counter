from datetime import datetime, timezone
import os
import tempfile
import cv2
import json
import requests
from pathlib import Path
from worker.tray import Tray
from utils.video_utils import compute_iou, get_category, reduce_overexposed_regions, save_alarm
from utils.video_utils import get_category
from ultralytics import YOLO
from config import ALARM_CALLBACK_URL
import threading


class VideoProcessor:

    """
    Videoları işleyen, tepsi ve tabak tespiti yapan, gerekli durumlarda alarm ve görsel kayıt oluşturan sınıf.

    Args:
        model_path (str): YOLO model dosya yolu.
        video_dir (str): Video klasör yolu.
        proof_dir (str): Alarm görüntülerinin kaydedileceği klasör yolu.
        settings (dict): Cihaz, eşik, sınıf ID'leri ve parametreleri içeren yapılandırma.
    """

    def __init__(self, model_path, video_dir, proof_dir, settings):
        self.model = YOLO(model_path).to(settings["device"])
        self.video_dir = Path(video_dir)
        self.proof_dir = Path(proof_dir)
        self.settings = settings
        self.tray_counter = 1

    def process_video(self, video_path, transaction_uuid=None, origin_time=None):

        """
        Video dosyasını okur, kareleri işler, tepsi ve tabak tespiti yapar.

        Args:
            video_path (Path): İşlenecek video dosyasının yolu.
            transaction_uuid (str, optional): Görevle ilişkilendirilen benzersiz işlem kimliği.
            origin_time (str, optional): Görevin başlatıldığı zaman.
        """

        cap = cv2.VideoCapture(str(video_path))
        trays= {}
        print(f"\nVideo işleniyor: {video_path.name}")

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            cropped = reduce_overexposed_regions(frame[:, self.settings["crop_left"]:self.settings["crop_right"]])
            result = self.model.predict(cropped, conf=self.settings["conf_threshold"], verbose=False)[0]

            tray_boxes, plate_centers = self.extract_detections(result)
            matched_ids = self.update_trays(trays, tray_boxes)
            self.tray_counter += len(set(matched_ids) - trays.keys())

            for tid in list(trays.keys()):
                tray = trays[tid]
                if tid not in matched_ids:
                    self.handle_lost_tray(tray, tid, video_path, transaction_uuid, origin_time)
                else:
                    count = self.count_plates_in_tray(tray.box, plate_centers)
                    tray.update(count, frame)

            if self.settings["show_window"]:
                self.display_frame(frame, trays)

        self.finalize_unalarmed(trays, video_path, transaction_uuid, origin_time)
        cap.release()
        print(f"Video tamamlandı: {video_path.name}")
        cv2.destroyAllWindows()

    def extract_detections(self, result):

        """
        YOLO çıktısından tepsi ve tabak tespitlerini ayıklar.

        Args:
            result (YOLO.Result): YOLO modelinin döndürdüğü sonuç nesnesi.

        Returns:
            tuple: [(x1, y1, x2, y2)] formatında tepsi box'ları ve [(cx, cy)] formatında tabak merkezleri listesi.
        """

        trays, plates = [], []
        for r in result.boxes:
            cls = int(r.cls[0])
            x1, y1, x2, y2 = map(int, r.xyxy[0])
            x1 += self.settings["crop_left"]
            x2 += self.settings["crop_left"]
            if cls == self.settings["tray_class"]:
                trays.append((x1, y1, x2, y2))
            elif cls == self.settings["plate_class"]:
                plates.append(((x1 + x2) // 2, (y1 + y2) // 2))
        return trays, plates

    def update_trays(self, trays, tray_boxes):

        """
        Yeni bulunan tepsi kutularını mevcut izlenen tepsilerle eşleştirir veya yenilerini ekler.

        Args:
            trays (dict): Mevcut izlenen tepsi sözlüğü.
            tray_boxes (list): Yeni tespit edilen tepsi kutuları.

        Returns:
            list: Eşleşen tepsi ID’leri.
        """

        matched = []
        for box in tray_boxes:
            matched_id = next((tid for tid, tray in trays.items() if compute_iou(tray.box, box) > 0.4), None)
            if matched_id:
                trays[matched_id].box = box
                trays[matched_id].lost = 0
                matched.append(matched_id)
            else:
                trays[self.tray_counter] = Tray(box, self.settings["stable_confirm_frames"])
                matched.append(self.tray_counter)
                print(f"++Yeni tepsi: ID {self.tray_counter}")
                self.tray_counter += 1
        return matched

    def handle_lost_tray(self, tray, tid, video_path, transaction_uuid, origin_time):
        
        """
        Görüntüden kaybolan ve alarm durumu oluşabilecek tepsileri işler.

        Args:
            tray (Tray): Kaybolan tepsi nesnesi.
            tid (int): Tepsi kimliği.
            video_path (Path): İşlenen video yolu.
            transaction_uuid (str): Görev kimliği.
            origin_time (str): Görevin başlangıç zamanı.
        """
        
        tray.lost += 1
        if tray.lost > self.settings["max_lost"] and not tray.alarmed and tray.image is not None:
            self.save_proof(tray, tid, video_path, transaction_uuid, origin_time)
            tray.alarmed = True

    def finalize_unalarmed(self, trays, video_path, transaction_uuid, origin_time):

        """
        Videonun sonunda alarm verememiş ama görüntüsü alınmış tüm tepsileri işler.

        Args:
            trays (dict): Tüm tepsi nesneleri.
            video_path (Path): Video dosyasının yolu.
            transaction_uuid (str): Görev kimliği.
            origin_time (str): Görevin başlatıldığı zaman.
        """

        for tid, tray in trays.items():
            if not tray.alarmed and tray.image is not None:
                self.save_proof(tray, tid, video_path, transaction_uuid, origin_time, closing=True)

    def count_plates_in_tray(self, box, plate_centers):

        """
        Verilen bir tepsi kutusu içinde kaç tabak olduğunu sayar.

        Args:
            box (tuple): Tepsi kutusu koordinatları (x1, y1, x2, y2).
            plate_centers (list): Tüm tabakların merkez koordinatları.

        Returns:
            int: Tepsinin içinde bulunan tabak sayısı.
        """

        x1, y1, x2, y2 = box
        return sum(1 for cx, cy in plate_centers if x1 <= cx <= x2 and y1 <= cy <= y2)

    def save_proof(self, tray, tid, video_path, transaction_uuid=None, origin_time=None, closing=False):

        """
        Alarm durumu oluştuğunda (veya kapanışta) görüntüyü kaydeder ve webhook'a alarm verisi gönderir.

        Args:
            tray (Tray): Alarm tetikleyen tepsi nesnesi.
            tid (int): Tepsi kimliği.
            video_path (Path): Video dosya yolu.
            transaction_uuid (str): Görev kimliği.
            origin_time (str): Başlangıç zamanı.
            closing (bool): Kapanışta mı kayıt alındığını belirtir.
        """

        cat = get_category(tray.max_count)

        proof_cat_dir = self.proof_dir / cat
        proof_cat_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{video_path.stem}_tray{tid}_cat{cat}.jpg"
        proof_file_path = proof_cat_dir / filename

        image = tray.image.copy()

        cv2.imwrite(str(proof_file_path), image)
        print(f"{'(Kapanış) ' if closing else ''}ALARM görüntüsü kaydedildi: {proof_file_path}")


        proof_url = f"http://localhost:8000/proofs/{cat}/{filename}"


        origin_time = datetime.now(timezone.utc).isoformat()
        if transaction_uuid and origin_time:
            alarm_payload = {
                "transaction_uuid": transaction_uuid,
                "proof_url": proof_url,
                "item_category": cat,
                "origin_time": origin_time
            }

            print("Alarm JSON:", json.dumps(alarm_payload, indent=2))
            threading.Thread(target=self.send_alarm_async, args=(alarm_payload,), daemon=True).start()
            threading.Thread(target=save_alarm, args=(alarm_payload,), daemon=True).start()


    def display_frame(self, frame, trays):

        """
        İzleme penceresinde anlık kareyi ve tepsi etiketlerini gösterir.

        Args:
            frame (np.ndarray): Video karesi.
            trays (dict): Tüm tepsi nesneleri.
        """

        for tid, tray in trays.items():
            if tray.lost <= self.settings["max_lost"]:
                x1, y1, x2, y2 = tray.box
                label = f"ID {tid} | {tray.max_count} tabak | {get_category(tray.max_count)}"
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        cv2.imshow("İşlenen Görüntü", frame)
        cv2.waitKey(1)

    def process_video_by_url(self, video_url: str, transaction_uuid: str, origin_time: str):

        """
        URL'den video dosyasını indirir, geçici dosyaya yazar ve işleme başlatır.

        Args:
            video_url (str): Video dosyasının uzaktan URL’si.
            transaction_uuid (str): Görev kimliği.
            origin_time (str): Görev başlangıç zamanı.
        """

        cap = cv2.VideoCapture(video_url)
        if not cap.isOpened():
            print(f"Video açılamadı: {video_url}")
            return

        temp_video_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
        print(f"Video indiriliyor ve geçici dosyaya yazılıyor: {temp_video_path}")

        writer = cv2.VideoWriter(temp_video_path, cv2.VideoWriter_fourcc(*'mp4v'), 30,
                                 (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            writer.write(frame)

        cap.release()
        writer.release()

        try:
            self.process_video(Path(temp_video_path), transaction_uuid=transaction_uuid, origin_time=origin_time)
        finally:
            # Video işlense de hata olsa da geçici dosyayı sil
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
                print(f"Geçici dosya silindi: {temp_video_path}")

    def send_alarm_async(self, payload):

        """
        Alarm verisini asenkron olarak webhook'a gönderir.

        Args:
            payload (dict): Gönderilecek alarm JSON içeriği.
        """

        try:
            requests.post(ALARM_CALLBACK_URL, json=payload, timeout=5)
        except Exception as e:
            print(f"Alarm gönderilemedi: {e}")