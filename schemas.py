"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict

# Example schemas (keep for reference)
class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Video processing app schemas

class Job(BaseModel):
    """
    Video processing jobs created when a user uploads a source video OR provides
    a YouTube URL, then requests a short clip with certain duration, subtitle
    mode, language, styling, and post-edit options.

    Collection name: "job"
    """
    # Source
    source_type: Literal['upload','youtube'] = Field('upload', description="Where the source video comes from")
    filename: Optional[str] = Field(None, description="Original uploaded filename if uploaded")
    youtube_url: Optional[str] = Field(None, description="YouTube URL if provided")
    stored_path: Optional[str] = Field(None, description="Server path for the fetched/uploaded source file")

    # Outputs
    output_path: Optional[str] = Field(None, description="Server path to processed output video")
    subtitle_path: Optional[str] = Field(None, description="Server path to generated/provided SRT file")

    # Core options
    duration_seconds: int = Field(..., ge=5, le=180, description="Target duration for the short video")
    subtitle_mode: Literal['none','auto','custom'] = Field('none', description="How subtitles are generated")
    custom_subtitle_text: Optional[str] = Field(None, description="User-provided subtitle text if any")
    subtitle_language: Optional[str] = Field(None, description="Language code or name for subtitles (e.g., en, id)")

    # Styling presets and post-editing controls
    subtitle_template: Optional[str] = Field(None, description="Preset key for subtitle style/template")
    subtitle_position: Optional[Literal['top','middle','bottom']] = Field('bottom', description="General position of subtitles")
    subtitle_offset_y: Optional[int] = Field(0, description="Vertical offset in pixels from chosen anchor")
    video_effects: Optional[List[str]] = Field(default_factory=list, description="List of video effect keys to apply")
    aspect_ratio: Optional[Literal['9:16','1:1','4:5','16:9']] = Field('9:16', description="Output aspect ratio")
    resolution: Optional[Literal['720p','1080p']] = Field('1080p', description="Output resolution preset")
    hard_subtitles: Optional[bool] = Field(False, description="Whether to burn subtitles into the video")

    # Status & metrics
    status: Literal['pending','processing','done','error'] = Field('pending', description="Processing status")
    error_message: Optional[str] = Field(None, description="Error details if processing fails")
    viral_score: Optional[float] = Field(None, ge=0, le=100, description="Heuristic score for virality")

    # Public URLs
    download_url: Optional[str] = Field(None, description="Public URL to download the processed video")
    subtitle_url: Optional[str] = Field(None, description="Public URL to download the SRT file if available")

# Add more schemas as needed
