import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    country_code: str
    phone_number: str
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    is_profile_complete: bool
    display_name: str
    created_at: datetime
    updated_at: datetime


class UserProfileUpdate(BaseModel):
    """Body for PATCH /users/me — all fields optional so partial updates work."""

    first_name: str | None = Field(default=None, min_length=1, max_length=100, examples=["Tarun"])
    last_name: str | None = Field(default=None, min_length=1, max_length=100, examples=["Sharma"])
    email: EmailStr | None = Field(default=None, examples=["tarun@example.com"])
