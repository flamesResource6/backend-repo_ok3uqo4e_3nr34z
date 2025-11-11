import os
import uuid
from typing import Optional, List

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


def compute_viral_score(name: str, duration: int) -> float:
    # Simple heuristic score 0-100
    base = min(100, max(0, 20 + duration))
    if any(k in (name or "").lower() for k in ["wow", "amazing", "hack", "viral", "money", "tips"]):
        base += 15
    return float(min(100, base))


@app.post("/api/jobs", response_model=JobResponse)
async def create_job(
    # Source selection
    source_type: str = Form("upload"),  # upload | youtube
    file: UploadFile | None = File(None),
    youtube_url: Optional[str] = Form(None),

    # Core options
    duration_seconds: int = Form(..., ge=5, le=180),
    subtitle_mode: str = Form("none"),  # none | auto | custom
    custom_subtitle_text: Optional[str] = Form(None),
    subtitle_language: Optional[str] = Form(None),

    # Styling / post-editing
    subtitle_template: Optional[str] = Form(None),
    subtitle_position: Optional[str] = Form("bottom"),  # top | middle | bottom
    subtitle_offset_y: int = Form(0),
    video_effects: Optional[str] = Form(""),   # comma-separated keys
    aspect_ratio: Optional[str] = Form("9:16"),
    resolution: Optional[str] = Form("1080p"),
    hard_subtitles: bool = Form(False),
):
    if subtitle_mode not in {"none", "auto", "custom"}:
        raise HTTPException(status_code=400, detail="Invalid subtitle_mode")
    if source_type not in {"upload", "youtube"}:
        raise HTTPException(status_code=400, detail="Invalid source_type")

    job_id = str(uuid.uuid4())

    # Handle source acquisition
    original_name = None
    stored_path = None

    if source_type == "upload":
        if file is None:
            raise HTTPException(status_code=400, detail="File is required for upload source")
        original_name = file.filename
        stored_name = f"{job_id}_{original_name}"
        stored_path = os.path.join(UPLOAD_DIR, stored_name)
        with open(stored_path, "wb") as f:
            f.write(await file.read())
    else:  # youtube
        if not youtube_url:
            raise HTTPException(status_code=400, detail="youtube_url is required for youtube source")
        # Simulate fetching the YouTube video by writing a placeholder mp4
        original_name = f"youtube_{job_id}.mp4"
        stored_path = os.path.join(UPLOAD_DIR, original_name)
        with open(stored_path, "wb") as f:
            f.write(f"SIMULATED_YT_DOWNLOAD from {youtube_url}".encode("utf-8"))

    # Simulate processing output
    output_video_path = os.path.join(OUTPUT_DIR, f"{job_id}.mp4")
    with open(output_video_path, "wb") as f:
        # Include some bytes encoding settings to make the file non-empty
        meta = (
            f"OUTPUT|ratio={aspect_ratio}|res={resolution}|effects={video_effects}|"
            f"hard_sub={hard_subtitles}|pos={subtitle_position}:{subtitle_offset_y}|tpl={subtitle_template}\n"
        )
        f.write(meta.encode("utf-8"))
        f.write(b"FAKE_MP4_DATA")

    subtitle_file_path = None
    if subtitle_mode in {"auto", "custom"}:
        subtitle_file_path = os.path.join(SUB_DIR, f"{job_id}.srt")
        text = custom_subtitle_text or f"Auto-generated subtitles ({subtitle_language or 'auto'})"
        # Simple single-cue SRT with style hint in a comment line
        with open(subtitle_file_path, "w", encoding="utf-8") as f:
            f.write("1\n00:00:00,000 --> 00:00:02,000\n")
            f.write(text + "\n")
            style_hint = f"# style template={subtitle_template or 'default'}, position={subtitle_position}, offsetY={subtitle_offset_y}\n"
            f.write(style_hint)

    # Compute a viral score
    name_for_score = original_name or youtube_url or "video"
    score = compute_viral_score(name_for_score, duration_seconds)

    # Parse effects string to list for storage consistency
    effects_list: List[str] = [e.strip() for e in (video_effects or "").split(",") if e.strip()]

    # Persist job
    job = Job(
        source_type=source_type,
        filename=original_name,
        youtube_url=youtube_url,
        stored_path=stored_path,
        output_path=output_video_path,
        subtitle_path=subtitle_file_path,
        duration_seconds=duration_seconds,
        subtitle_mode=subtitle_mode,
        custom_subtitle_text=custom_subtitle_text,
        subtitle_language=subtitle_language,
        subtitle_template=subtitle_template,
        subtitle_position=subtitle_position if subtitle_position in {"top","middle","bottom"} else "bottom",
        subtitle_offset_y=subtitle_offset_y,
        video_effects=effects_list,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        hard_subtitles=hard_subtitles,
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
