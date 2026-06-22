"""Room schemas for request/response validation."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class RoomCreate(BaseModel):
    """Schema for creating a new room."""
    id: str = Field(..., min_length=1, max_length=20, description="Room ID/Number, e.g. 101")
    name: str = Field(..., min_length=1, max_length=100, description="e.g. Deluxe City View")
    type: str = Field(..., min_length=1, max_length=100, description="e.g. Deluxe Room · Floor 3")
    price: float = Field(..., gt=0, description="Nightly price, must be positive")
    status: Optional[str] = "avail"  # "avail", "booked", "maint"
    cls: Optional[str] = "r1"
    feats: Optional[List[str]] = []
    fcls: Optional[List[str]] = []


class RoomUpdate(BaseModel):
    """Schema for updating a room (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[float] = Field(None, gt=0)
    status: Optional[str] = None  # "avail", "booked", "maint"
    cls: Optional[str] = None
    feats: Optional[List[str]] = None
    fcls: Optional[List[str]] = None


class RoomStatusUpdate(BaseModel):
    """Schema for the PATCH room status endpoint — typed replacement for raw dict."""
    status: str = Field(..., description="Must be one of: avail, booked, maint")


class RoomResponse(BaseModel):
    """Schema for room response."""
    id: str
    name: str
    type: str
    price: float
    status: str
    cls: str
    feats: List[str]
    fcls: List[str]
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}
