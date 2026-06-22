"""User database model."""
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, BeforeValidator
from typing_extensions import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]


class UserDB(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    email: EmailStr
    hashed_password: str
    role: str = "staff"  # "admin" or "staff"
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}
