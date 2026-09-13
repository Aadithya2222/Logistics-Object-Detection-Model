"""
app/schemas.py
Pydantic models for API request/response shapes.
"""

from pydantic import BaseModel, Field
from typing import Literal


class BBox(BaseModel):
    x1: float = Field(..., description="Left pixel coordinate")
    y1: float = Field(..., description="Top pixel coordinate")
    x2: float = Field(..., description="Right pixel coordinate")
    y2: float = Field(..., description="Bottom pixel coordinate")


class Detection(BaseModel):
    cls: str = Field(..., alias="class", description="Detected class name")
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: BBox

    model_config = {"populate_by_name": True}


class DetectResponse(BaseModel):
    objects: list[Detection]
    num_detections: int
    image_size: tuple[int, int] = Field(..., description="(width, height)")


class AskResponse(BaseModel):
    answer: str
    used_detector: bool
    confidence: Literal["high", "medium", "low"]
    detections: list[Detection] | None = None
    intent: str | None = None
