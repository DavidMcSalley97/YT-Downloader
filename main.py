import asyncio
import json
import os
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import subprocess
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel


# ------------------------
# APP / CORS
# ------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten later
    allow_credentials=False,      # set True only if using cookies/auth headers
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# active_jobs[job_id] = {"progress": int, "done": bool, "error": str|None, "log": str}
active_jobs: Dict[str, Dict[str, Any]] = {}

# Optional: cookies and js runtimes for yt-dlp
COOKIES_FILE = os.getenv("YTDLP_COOKIES", "cookies.txt")
JS_RUNTIMES = os.getenv("YTDLP_JS_RUNTIMES", "").strip()  # e.g. "deno" or "node:/usr/bin/node"


# ------------------------
# REQUEST MODELS
# ------------------------
class ResolveRequest(BaseModel):
    lines: List[str]


class DownloadRequest(BaseModel):
    url: str
    mode: str = "audio"    # "audio" or "video"
    quality: str = "320"   # audio: 320/192/128, video: best/1080/720


# ------------------------
# HELPERS
# ------------------------
def _duration_str(sec: int) -> str:
    if not sec:
        return "Unknown"
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def yt_dlp_extra_args() -> List[str]:
    """
    Adds cookies + JS runtime args if available.
    This is the key to bypassing the YouTube "not a bot" prompt in many environments.
    """
    args: List[str] = []

    # Cookies
    if COOKIES_FILE and Path(COOKIES_FILE).exists():
        args += ["--cookies", COOKIES_FILE]

    # JS runtimes (optional)
    if JS_RUNTIMES:
        args += ["--js-runtimes", JS_RUNTIMES]

    return args


def yt_dlp_json(url: str) -> Dict[str, Any]:
    """
    Equivalent to your PyQt 'yt-dlp -j URL' with extra args.
    Raises RuntimeError with useful message.
    """
    cmd = ["yt-dlp", "-j", *yt_dlp_extra_args(), url]
    p = subprocess.run(cmd, capture_output=True, text=True)

    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()

    if p.returncode != 0:
        # Prefer stderr if present; yt-dlp often writes important errors there
        msg = err or out or f"yt-dlp failed with code {p.returncode}"
        raise RuntimeError(msg)

    if not out:
        raise RuntimeError("yt-dlp returned no JSON output")

    return json.loads(out)


def _make_job(job_id: str) -> None:
    active_jobs[job_id] = {
        "progress": 0,
        "done": False,
        "error": None,
        "log": "",
    }


# ------------------------
# ENDPOINTS
# ------------------------
@app.get("/health")
def health():
    return JSONResponse({"ok": True})


@app.post("/resolve")
async def resolve(req: ResolveRequest):
    """
    Like SmartSearchWorker:
    - if line starts with http -> use it
    - else ytsearch1:<query> and return webpage_url
    """
    resolved: List[str] = []

    for raw in req.lines:
        text = (raw or "").strip()
        if not text:
            continue

        if text.startswith("http"):
            resolved.append(text)
            continue

        try:
            cmd = ["yt-dlp", "-j", *yt_dlp_extra_args(), f"ytsearch1:{text}"]
            p = subprocess.run(cmd, capture_output=True, text=True)

            if p.returncode == 0 and (p.stdout or "").strip():
                data = json.loads(p.stdout)
                u = data.get("webpage_url")
                if u:
                    resolved.append(u)
        except Exception:
            # silent like your PyQt worker
            pass

    # unique preserve order
    seen = set()
    out: List[str] = []
    for u in resolved:
        if u not in seen:
            seen.add(u)
            out.append(u)

    return {"urls": out}


@app.get("/info")
async def info(url: str):
    """
    Like MediaInfoWorker:
    - returns title/uploader/duration/view_count/thumbnail
    - on failure returns {"error": "..."} (frontend can display)
    """
    try:
        data = yt_dlp_json(url)
        dur = int(data.get("duration") or 0)
        return {
            "title": data.get("title"),
            "uploader": data.get("uploader"),
            "duration": dur,
            "duration_str": _duration_str(dur),
            "view_count": data.get("view_count", 0),
            "thumbnail": data.get("thumbnail"),
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/download")
async def download(req: DownloadRequest):
    if not req.url or not req.url.strip():
        raise HTTPException(status_code=400, detail="url is required")

    job_id = str(uuid.uuid4())
    _make_job(job_id)

    asyncio.create_task(_run_download(job_id, req.url.strip(), req.mode, req.quality))
    return {"job_id": job_id}


async def _run_download(job_id: str, url: str, mode: str, quality: str):
    """
    Runs yt-dlp and updates active_jobs progress + error.
    MOST IMPORTANT FIX:
    - capture last output line into active_jobs[job_id]["log"]
    - if return code != 0, set active_jobs[job_id]["error"] = last log line
    """
    try:
        template = str(DOWNLOAD_DIR / "%(title)s.%(ext)s")
        extra = yt_dlp_extra_args()

        if mode == "audio":
            cmd = [
                "yt-dlp",
                *extra,
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", quality,
                "--no-playlist",
                "-o", template,
                url,
            ]
        else:
            fmt = "bestvideo+bestaudio/best" if quality == "best" else f"bv*[height<={quality}]+ba/b"
            cmd = [
                "yt-dlp",
                *extra,
                "-f", fmt,
                "--merge-output-format", "mp4",
                "--no-playlist",
                "-o", template,
                url,
            ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        percent_re = re.compile(r"(\d+(?:\.\d+)?)%")

        while True:
            line = await proc.stdout.readline()
            if not line:
                break

            s = line.decode(errors="ignore").strip()
            if s:
                active_jobs[job_id]["log"] = s  # keep last meaningful line

            m = percent_re.search(s)
            if m:
                active_jobs[job_id]["progress"] = int(float(m.group(1)))

        rc = await proc.wait()

        if rc != 0:
            # This is what fixes "no errors but not downloading"
            last = active_jobs[job_id].get("log") or ""
            # If YouTube bot block appears, it will be here.
            active_jobs[job_id]["error"] = last or f"yt-dlp failed (code {rc})"

        # If successful, make sure progress ends at 100
        if not active_jobs[job_id].get("error"):
            active_jobs[job_id]["progress"] = 100

        active_jobs[job_id]["done"] = True

    except Exception as e:
        active_jobs[job_id]["error"] = str(e)
        active_jobs[job_id]["done"] = True


@app.websocket("/ws/{job_id}")
async def ws(websocket: WebSocket, job_id: str):
    await websocket.accept()

    if job_id not in active_jobs:
        await websocket.send_json({"error": "Unknown job_id", "done": True})
        await websocket.close()
        return

    try:
        while True:
            job = active_jobs.get(job_id)
            if not job:
                await websocket.send_json({"error": "Job disappeared", "done": True})
                break

            payload = {"progress": job.get("progress", 0)}

            # push errors to the UI (CRITICAL)
            if job.get("error"):
                payload["error"] = job["error"]
                payload["done"] = True
                await websocket.send_json(payload)
                break

            if job.get("done"):
                payload["done"] = True
                await websocket.send_json(payload)
                break

            await websocket.send_json(payload)
            await asyncio.sleep(0.5)

    except WebSocketDisconnect:
        return
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


@app.get("/files/{filename}")
def files(filename: str):
    fp = DOWNLOAD_DIR / filename
    if not fp.exists() or not fp.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(fp), filename=filename)


@app.get("/speed")
def speed():
    # placeholder; your UI expects download/upload/ping keys
    return {"download": "n/a", "upload": "n/a", "ping": "n/a"}


# Debug endpoints to see what's happening instantly
@app.get("/debug/jobs")
def debug_jobs():
    return active_jobs


@app.get("/job/{job_id}")
def job(job_id: str):
    return active_jobs.get(job_id, {"error": "unknown job_id"})


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=False)

