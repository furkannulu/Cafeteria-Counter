from datetime import time
import torch
from utils.redis_queue import dequeue_task
from worker.video_processor import VideoProcessor
from config import *

settings = {
    "device": "cuda" if torch.cuda.is_available() else "cpu",  # GPU varsa kullan
    "tray_class": 0,  # YOLO modelindeki tepsi sınıfı
    "plate_class": 1,  # YOLO modelindeki tabak sınıfı
    "conf_threshold": 0.6,  # YOLO için minimum güven skoru
    "crop_left": 250,  # Görüntünün solundan kırpılacak piksel sayısı
    "crop_right": 1750,  # Görüntünün sağından kırpılacak piksel sayısı
    "stable_confirm_frames": 2,  # Tabak sayısının sabitlenmesi için gereken ardışık kare sayısı
    "max_lost": 10,  # Bir tepsinin kayıp sayılmadan önce kaybolabileceği maksimum kare sayısı
    "show_window": True  # `True`: GUI ile göster, `False`: headless (sunucu için)
}

# Video işleyiciyi başlat
processor = VideoProcessor(
    model_path="detector.pt",               # YOLOv12 model ağırlıkları
    video_dir=VIDEO_DOWNLOAD_DIR,          # Videoların indirildiği klasör
    proof_dir=PROOF_DIR,                   # Alarm görüntülerinin kaydedileceği klasör
    settings=settings
)

# Sonsuz döngü: Redis kuyruğundan görev al ve işle
while True:
    task = dequeue_task()
    if task:
        print(f"Video kuyruğundan alındı: {task['video_url']}")
        processor.process_video_by_url(
            video_url=task["video_url"],
            transaction_uuid=task["transaction_uuid"],
            origin_time=task["origin_time"]
        )
    else:
        print("Task Bekleniyor.")
