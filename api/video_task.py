"""

Bu modül, bir video işleme görevini Redis kuyruğuna ekler.
FastAPI üzerinden çağrıldığında, video URL'si ve meta veriler ile birlikte
işleme kuyruğuna alınır.

"""

import traceback
from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, HttpUrl
from redis import Redis
from typing import Optional
import uuid
import json
import os
from datetime import datetime, timezone

redis_conn = Redis(host="localhost", port=6379, db=0)

router = APIRouter()


class VideoPayload(BaseModel):
    """
    Video işleme görevi için gelen JSON payload yapısı.

    """
    transaction_uuid: str
    video_url: HttpUrl
    origin_time: Optional[str] = None

@router.post("/video-task/")
async def enqueue_video_task(payload: VideoPayload):

    """
    Video işleme görevini Redis kuyruğuna ekler.

    Args:
        payload (VideoPayload): video URL'si ve meta verileri içeren istek

    Returns:
        dict: görev durumu ve üretilen task ID
    """
    try:
        task_data = jsonable_encoder(payload)

        if not task_data.get("origin_time"):
            task_data["origin_time"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        task_data["task_id"] = str(uuid.uuid4())
        redis_conn.lpush("video_tasks", json.dumps(task_data))
        return {"status": "queued", "task_id": task_data["task_id"]}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
