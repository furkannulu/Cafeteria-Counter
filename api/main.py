"""
Bu modül, FastAPI tabanlı Cafeteria Counter API uygulamasının giriş noktasıdır.

İşlevler:
- FastAPI uygulamasını başlatır.
- `api.routes` modülündeki tüm API rotalarını projeye dahil eder.

Başlatıldığında:
- API dökümantasyonu `/docs` altında Swagger UI ile görüntülenebilir.
- API metadata'sı `title="Cafeteria Counter API"` olarak tanımlanmıştır.

Kullanım:
    uvicorn run:app --reload
"""


from fastapi import FastAPI
from api.routes import router

app = FastAPI(title="Cafeteria Counter API")
app.include_router(router)
