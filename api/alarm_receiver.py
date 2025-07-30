from collections import defaultdict
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List

"""
Bu modül, video işleme sisteminde oluşan alarmların yönetimi için FastAPI rotalarını içerir.

Fonksiyonlar:
- `/alarm/` (POST): Yeni alarm verisi alır ve bellekte saklar. Aynı alarm birden fazla kez eklenmez.
- `/alarms/` (GET): Kaydedilmiş tüm alarmları JSON formatında döner.
- `/proofs-list` (GET, HTML): Alarm görüntülerini kategoriye göre gruplayarak görsel olarak sunar.
- `/alarms/clear` (DELETE): Tüm kayıtlı alarmları sıfırlar.

Veri Modeli:
- `AlarmPayload`: Alarm içeriğini temsil eden `transaction_uuid`, `proof_url`, `item_category`, `origin_time` alanlarını içerir.
"""

router = APIRouter()

class AlarmPayload(BaseModel):
    transaction_uuid: str
    proof_url: str
    item_category: str
    origin_time: str

alarms: List[AlarmPayload] = []  

@router.get("/alarms/")
async def list_alarms():
    return alarms

@router.get("/proofs-list", response_class=HTMLResponse)
async def show_proofs():
    categorized = defaultdict(list)
    for alarm in alarms:
        key = (alarm.proof_url, alarm.item_category)
        if key not in categorized[alarm.item_category]:
            categorized[alarm.item_category].append(alarm.proof_url)

    html = "<h2>Proof Images</h2>"
    for category, urls in categorized.items():
        html += f"<h3>{category}</h3><ul style='list-style-type:none; padding-left:0;'>"
        for url in urls:
            html += f'''
            <li style="margin-bottom:10px;">
                <a href="{url}" target="_blank">
                    <img src="{url}" alt="{category}" width="320" style="border:1px solid #ccc;"/>
                </a>
            </li>
            '''
        html += "</ul>"
    return html


@router.delete("/alarms/clear")
async def clear_alarms():
    alarms.clear()
    return {"status": "cleared"}