"""

Bu modül, dış sistemlerden gelen video işleme isteklerini karşılar.
İstek verisi Redis kuyruğuna eklenir.

"""

from fastapi import APIRouter
from api.models import TriggerRequest
from utils.redis_queue import enqueue_task
from fastapi.encoders import jsonable_encoder
from uuid import uuid4


router = APIRouter()


@router.post("/trigger")
async def trigger_processing(req: TriggerRequest):
    """
    
    Bu endpoint, gelen video işleme isteğini Redis kuyruğuna ekler.
    İstek başarılı şekilde kuyruğa eklendiyse, 'queued' yanıtı döner.

    Args:
        req (TriggerRequest): transaction_uuid, video_url ve origin_time içeren istek objesi

    Returns:
        dict: Kuyruğa alındı mesajı ve işlem UUID’si
    """
    data = jsonable_encoder(req)

    if not data.get("transaction_uuid"):
        data["transaction_uuid"] = str(uuid4())

    enqueue_task(data)
    return {"status": "queued", "transaction_uuid": data["transaction_uuid"]}