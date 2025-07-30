"""
Bu modül, API için kullanılan veri modellerini (`BaseModel`) tanımlar.
- `TriggerRequest`: Video işleme tetikleme istekleri için gelen veriyi doğrular.
- `AlarmPayload`: Alarm verisini temsil eder ve doğrular.

Bu modeller, veri bütünlüğü sağlamak ve API giriş/çıkışlarını yapılandırmak için kullanılır.
"""

from pydantic import BaseModel, HttpUrl
from datetime import datetime

class TriggerRequest(BaseModel):
    transaction_uuid: str
    video_url: HttpUrl
    origin_time: datetime

class AlarmPayload(BaseModel):
    transaction_uuid: str
    proof_url: str
    item_category: str
    origin_time: datetime
