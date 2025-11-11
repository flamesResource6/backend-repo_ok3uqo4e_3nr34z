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
from typing import Optional, Literal, List

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Video processing app schemas

class Job(BaseModel):
    """
    Video processing jobs created when a user uploads a source video and requests
    a short clip with certain duration, subtitle mode, and other options.

    Collection name: "job"
    """
    filename: str = Field(..., description="Original uploaded filename")
    stored_path: str = Field(..., description="Server path for the uploaded file")
    output_path: Optional[str] = Field(None, description="Server path to processed output video")
    subtitle_path: Optional[str] = Field(None, description="Server path to generated/provided SRT file")
    duration_seconds: int = Field(..., ge=5, le=180, description="Target duration for the short video")
    subtitle_mode: Literal['none','auto','custom'] = Field('none', description="How subtitles are generated")
    custom_subtitle_text: Optional[str] = Field(None, description="Optional user-provided subtitle text to generate SRT")
    status: Literal['pending','processing','done','error'] = Field('pending', description="Processing status")
    error_message: Optional[str] = Field(None, description="Error details if processing fails")
    viral_score: Optional[float] = Field(None, ge=0, le=100, description="Heuristic score for virality")
    download_url: Optional[str] = Field(None, description="Public URL to download the processed video")
    subtitle_url: Optional[str] = Field(None, description="Public URL to download the SRT file if available")

# Add your own schemas here:
# --------------------------------------------------

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
