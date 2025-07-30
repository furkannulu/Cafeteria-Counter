# Tepsi ve Tabak Tespit Sistemi (YOLOv12)

Bu proje, YOLOv12 modelini kullanarak video dosyaları üzerinde tepsi ve üzerindeki tabakları tespit etmek üzere geliştirilmiştir. FastAPI tabanlı API yapısı ile çalışır. Videolar kuyruğa alınır, Redis üzerinden işleme gönderilir ve sonuç olarak alarm durumları JSON formatında kaydedilir.

## Özellikler

- FastAPI ile RESTful API yapısı
- Redis ile görev kuyruğu yönetimi
- YOLOv12 ile gerçek zamanlı nesne tespiti
- Tepsilere benzersiz ID atanması ve tabak sayımı
- Alarm sonrası kanıt görseli kaydı ve JSON loglama
- Geçici video dosyalarının otomatik silinmesi

## Teknolojiler

- Python 3.10+
- OpenCV
- Ultralytics YOLOv12
- Redis
- FastAPI
- Pydantic
- Uvicorn

## Proje Yapısı

Cafeteria-Counter/
│
├── api/ # FastAPI endpoint'leri
│ ├── alarm_receiver.py # Alarm JSON kayıtlarını alır
│ ├── main.py # FastAPI uygulama başlatıcı
│ └── video_task.py # Redis'e video işleme görevi ekler
│
├── worker/ # Video işleme mantığı
│ ├── tray.py # Tepsi takip ve veri yapısı
│ └── video_processor.py # YOLO ile tespit ve alarm üretimi
│
├── utils/ # Yardımcı araçlar
│ ├── redis_queue.py # Redis bağlantı ve kuyruk fonksiyonları
│ └── video_utils.py # Video ön işleme (ışık düzeltme, iou hesaplama)
│
├── videos/ # İşlenecek videoların bulunması gereken klasör
├── proofs/ # Alarm durumlarında oluşturulan kanıt resimleri
├── alarms/ # Alarm loglarının JSON olarak tutulduğu klasör
│
├── detector.pt # YOLOv12 ağırlık dosyası
├── config.py # Ayarlar (model yolu, eşik değerler vs.)
├── run.py # Worker (işçi) başlatıcı
├── main.py # (Eski, büyük ihtimalle legacy giriş noktası)
│
├── LICENSE # Lisans dosyası
├── README.md # Proje açıklaması
├── requirements.txt # Gerekli Python kütüphaneleri
├── .gitignore # Versiyon kontrolüne dahil edilmeyecek dosyalar
└── .gitattributes # Git CRLF/LF yönetimi için dosya nitelikleri


## Akış Şeması

1. FastAPI başlatılır: ` uvicorn run:app --reload`
2. Redis manuel olarak açılır: `redis-server`
3. Ana akış dosyası çalıştırılır: `python Cafeteria-Counter/main.py`
4. `/video-task/` endpoint’ine aşağıdaki gibi istek atılır:
   - `video_url`: `http://localhost:8000/videos/test1.mp4`
   - `transaction_uuid`: alarm JSON dosya adı
5. Görev Redis kuyruğuna eklenir
6. Worker videoyu indirir (temp olarak)
7. Video işlenir (YOLOv12 ile tepsi & tabak tespiti)
8. Alarm üretilir:
   - Görsel: `proofs/`
   - JSON: `alarms/`
   - Görüntüleme: `/proofs-list` (önizlemeli), `/alarms/` (JSON)
9. Temp video silinir
    
## Ayarlar ve Hyperparametreler

- `conf_threshold`: Modelin tahmin güven eşiği
- `crop_left`, `crop_right`: Görüntüden işlenecek alan (ROI)
- `show_window`: İşlenen videoyu görsel olarak göstermek istenirse aktif edilir
- `max_lost`: Bir tepsinin kayboldu kabul edilmesi için gereken frame sayısı.

## Test 

Örnek istek:
```json
{
  "transaction_uuid": "abc123",
  "video_url": "http://localhost:8000/videos/test1.mp4",
  "origin_time": "2025-01-01T00:00:00Z"
}

!! Notlar

videos/ ve proofs/ klasörleri FastAPI üzerinden servis edilir.

Video URL'si hem tam URL "http://localhost:8000/videos/video_ismi.mp4" olarak gönderilmelidir.

Redis arka planda çalışıyor olmalıdır (redis-server).