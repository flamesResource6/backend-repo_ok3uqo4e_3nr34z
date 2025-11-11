import os
import uuid
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import Job

# Simple placeholder processors - in a real production system you would
# integrate with FFMPEG and a transcription model. Here we simulate processing
# and produce files so the app works end-to-end in the demo environment.

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
SUB_DIR = os.path.join(BASE_DIR, "subtitles")

for d in [UPLOAD_DIR, OUTPUT_DIR, SUB_DIR]:
    os.makedirs(d, exist_ok=True)


class JobResponse(BaseModel):
    id: str
    status: str
    viral_score: Optional[float] = None
    download_url: Optional[str] = None
    subtitle_url: Optional[str] = None


@app.get("/")
def read_root():
    return {"message": "Video AI Clipper API Ready"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
    }
    try:
        if db is not None:
            _ = db.list_collection_names()
            response["database"] = "✅ Connected"
    except Exception as e:
        response["database"] = f"⚠️ {str(e)[:60]}"
    return response


def compute_viral_score(filename: str, duration: int) -> float:
    # Simple heuristic score 0-100
    base = min(100, max(0, 20 + duration))
    if any(k in filename.lower() for k in ["wow", "amazing", "hack", "viral", "money", "tips"]):
        base += 15
    return float(min(100, base))


@app.post("/api/jobs", response_model=JobResponse)
async def create_job(
    file: UploadFile = File(...),
    duration_seconds: int = Form(..., ge=5, le=180),
    subtitle_mode: str = Form("none"),  # none | auto | custom
    custom_subtitle_text: Optional[str] = Form(None),
):
    if subtitle_mode not in {"none", "auto", "custom"}:
        raise HTTPException(status_code=400, detail="Invalid subtitle_mode")

    # Store uploaded file
    job_id = str(uuid.uuid4())
    filename = f"{job_id}_{file.filename}"
    stored_path = os.path.join(UPLOAD_DIR, filename)
    with open(stored_path, "wb") as f:
        f.write(await file.read())

    # Simulate processing: create a small text file representing the video output
    output_video_path = os.path.join(OUTPUT_DIR, f"{job_id}.mp4")
    with open(output_video_path, "wb") as f:
        f.write(b"FAKE_MP4_DATA")

    subtitle_file_path = None
    if subtitle_mode in {"auto", "custom"}:
        subtitle_file_path = os.path.join(SUB_DIR, f"{job_id}.srt")
        text = custom_subtitle_text or "Auto-generated subtitles"
        with open(subtitle_file_path, "w", encoding="utf-8") as f:
            f.write("1\n00:00:00,000 --> 00:00:02,000\n" + text + "\n")

    # Compute a viral score
    score = compute_viral_score(file.filename, duration_seconds)

    # Persist job
    job = Job(
        filename=file.filename,
        stored_path=stored_path,
        output_path=output_video_path,
        subtitle_path=subtitle_file_path,
        duration_seconds=duration_seconds,
        subtitle_mode=subtitle_mode,  
        custom_subtitle_text=custom_subtitle_text,
        status="done",
        viral_score=score,
        download_url=f"/api/download/{job_id}",
        subtitle_url=f"/api/subtitles/{job_id}" if subtitle_file_path else None,
    )
    job_id_db = create_document("job", job)

    return JobResponse(
        id=job_id_db,
        status=job.status,
        viral_score=score,
        download_url=job.download_url,
        subtitle_url=job.subtitle_url,
    )


@app.get("/api/download/{job_id}")
async def download_output(job_id: str):
    # In a production app, we'd query DB by _id. Here we map by filename pattern.
    path = os.path.join(OUTPUT_DIR, f"{job_id}.mp4")
    if not os.path.exists(path):
        # try to find by prefix
        candidates = [f for f in os.listdir(OUTPUT_DIR) if f.startswith(job_id)]
        if candidates:
            path = os.path.join(OUTPUT_DIR, candidates[0])
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="video/mp4", filename=f"clip_{job_id}.mp4")


@app.get("/api/subtitles/{job_id}")
async def download_subtitles(job_id: str):
    path = os.path.join(SUB_DIR, f"{job_id}.srt")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Subtitle not found")
    return FileResponse(path, media_type="text/plain", filename=f"subs_{job_id}.srt")


class JobsQuery(BaseModel):
    limit: Optional[int] = 20


@app.get("/api/jobs")
async def list_jobs(limit: Optional[int] = 20):
    try:
        docs = get_documents("job", {}, limit or 20)
        # Normalize ids as strings
        for d in docs:
            d["id"] = str(d.get("_id"))
            d.pop("_id", None)
        return {"items": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
