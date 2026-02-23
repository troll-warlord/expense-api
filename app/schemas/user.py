import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    country_code: str
    phone_number: str
    is_active: bool = True


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    is_profile_complete: bool
    display_name: str
    created_at: datetime
    updated_at: datetime


class UserProfileUpdate(BaseModel):
    """Body for PATCH /users/me — profile completion or update."""

    first_name: str = Field(..., min_length=1, max_length=100, examples=["Tarun"])
    last_name: str = Field(..., min_length=1, max_length=100, examples=["Sharma"])
    email: EmailStr = Field(..., examples=["tarun@example.com"])
