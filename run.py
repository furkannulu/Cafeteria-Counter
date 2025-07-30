import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from api import video_task, alarm_receiver

app = FastAPI(title="Cafeteria Counter API")

# Videolar klasörünü static olarak yayınla
os.makedirs("videos",exist_ok=True)
video_dir = os.path.join(os.getcwd(), "videos")
app.mount("/videos", StaticFiles(directory=video_dir), name="videos")

# Proofs klasörünü de static olarak yayınla
os.makedirs("proofs",exist_ok=True)
proof_dir = os.path.join(os.getcwd(), "proofs")
app.mount("/proofs", StaticFiles(directory=proof_dir), name="proofs")

# API route'larını ekle
app.include_router(video_task.router)
app.include_router(alarm_receiver.router)
