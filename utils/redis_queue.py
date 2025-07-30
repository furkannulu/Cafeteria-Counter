"""

Bu modül, video işleme görevlerini Redis üzerinde basit bir iş kuyruğunda
tutmak için kullanılır. Kuyruğa görev eklemek (`enqueue`) ve kuyruktan
görev almak (`dequeue`) fonksiyonları içerir.

"""

import redis
import json
from config import REDIS_URL

r = redis.Redis.from_url(REDIS_URL)

def enqueue_task(data: dict):
    
    """
    Görevi Redis kuyruğuna ekler (push/ FIFO).

    Args:
        data (dict): Kuyruğa eklenecek JSON formatında görev verisi.
    """

    r.rpush("video_tasks", json.dumps(data))

def dequeue_task():

    """
    Redis kuyruğundan bir görev çeker (pop).

    Returns:
        dict | None: Kuyruktan alınan görev verisi (JSON olarak çözülmüş),
                     veya belirlenen süre içinde görev alınamazsa None döner.
    """

    task = r.blpop("video_tasks", timeout=5)
    if task:
        _, raw = task
        return json.loads(raw)
    return None
