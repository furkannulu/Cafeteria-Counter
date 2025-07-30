import cv2

from utils.video_utils import get_category

class Tray:
    """
    Her bir tepsi nesnesini temsil eder. Tepsiye ait konum, maksimum tabak sayısı,
    alarm durumu ve kayıtlı görüntü gibi bilgileri içerir.
    """

    def __init__(self, box, stable_confirm_frames):

        """
        Tray sınıfının yapıcı metodu.

        Args:
            box (tuple): Tepsinin bounding box koordinatları (x1, y1, x2, y2).
            stable_confirm_frames (int): Tabak sayısının sabit kalması gereken kare sayısı.
        """

        self.box = box
        self.max_count = 0
        self.last_count = 0
        self.confirm_streak = 0
        self.image = None
        self.lost = 0
        self.alarmed = False
        self.stable_confirm_frames = stable_confirm_frames

    def update(self, count, full_frame):

        """
        Tepsiye ait tabak sayısını ve ilgili görüntüyü günceller.
        Yeterince kararlı (sabit) bir tabak sayısı tespit edildiğinde en net görüntü kaydedilir.

        Args:
            count (int): Bu karede tepsi içinde tespit edilen tabak sayısı.
            full_frame (numpy.ndarray): Mevcut video karesi (görüntü).
        """

        if count == self.last_count:
            self.confirm_streak += 1
        else:
            self.confirm_streak = 1
            self.last_count = count

        if self.confirm_streak >= self.stable_confirm_frames:
            if count > self.max_count:
                self.max_count = count
                x1, y1, x2, y2 = self.box
                blur = cv2.GaussianBlur(full_frame, (55, 55), 0)
                blur[y1:y2, x1:x2] = full_frame[y1:y2, x1:x2]
                label_text = f"ID | {count} tabak | {get_category(count)}"
                cv2.rectangle(blur, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(blur, label_text, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
                self.image = blur.copy()
                print(f"Tepsi güncellendi : Max count: {count}")
        else:
            print(f"Bekleniyor: {count} tabak (Streak: {self.confirm_streak})")
