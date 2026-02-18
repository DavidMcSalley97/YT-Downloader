import asyncio
import json
import os
import re
import uuid
import shutil
from pathlib import Path
from fastapi import FastAPI, WebSocket, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

active_jobs = {}

# ------------------------
# DOWNLOAD HANDLER
# ------------------------

async def run_download(job_id, url, mode, quality):
    template = str(DOWNLOAD_DIR / "%(title)s.%(ext)s")

    if mode == "audio":
        cmd = [
            "yt-dlp",
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", quality,
            "-o", template,
            url
        ]
    else:
        fmt = "bestvideo+bestaudio/best" if quality == "best" else f"bv*[height<={quality}]+ba/b"
        cmd = [
            "yt-dlp",
            "-f", fmt,
            "--merge-output-format", "mp4",
            "-o", template,
            url
        ]

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )

    active_jobs[job_id]["process"] = process

    while True:
        line = await process.stdout.readline()
        if not line:
            break

        decoded = line.decode()
        match = re.search(r"(\d+(?:\.\d+)?)%", decoded)
        if match:
            active_jobs[job_id]["progress"] = int(float(match.group(1)))

    await process.wait()
    active_jobs[job_id]["done"] = True

# ------------------------
# API ROUTES
# ------------------------

@app.post("/download")
async def start_download(data: dict):
    job_id = str(uuid.uuid4())
    active_jobs[job_id] = {
        "progress": 0,
        "done": False,
        "process": None
    }

    asyncio.create_task(
        run_download(
            job_id,
            data["url"],
            data["mode"],
            data["quality"]
        )
    )

    return {"job_id": job_id}

@app.websocket("/ws/{job_id}")
async def progress_ws(websocket: WebSocket, job_id: str):
    await websocket.accept()
    while not active_jobs[job_id]["done"]:
        await websocket.send_json({
            "progress": active_jobs[job_id]["progress"]
        })
        await asyncio.sleep(0.5)

    await websocket.send_json({"done": True})
    await websocket.close()

@app.get("/files/{filename}")
def download_file(filename: str):
    file_path = DOWNLOAD_DIR / filename
    return FileResponse(file_path)


@app.get("/speed")
def speed_test_placeholder():
    return {
        "download": "n/a",
        "upload": "n/a",
        "ping": "n/a",
        "note": "Speed test endpoint is a placeholder."
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=False)
