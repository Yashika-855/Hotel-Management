"""User schemas for request/response validation."""
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserRegister(BaseModel):
    """Schema for user registration. Role is always forced to 'staff' by the service."""
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128, description="Minimum 6 characters")
    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    role: str = Field("user", description="Account role: user or staff")


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    """Schema for user response (no password)."""
    id: str
    email: EmailStr
    role: str
    name: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
