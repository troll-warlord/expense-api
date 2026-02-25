import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    country_code: str | None = None
    phone_number: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_profile_complete: bool
    display_name: str
    created_at: datetime
    updated_at: datetime


class UserProfileUpdate(BaseModel):
    """Body for PATCH /users/me — all fields optional so partial updates work."""

    first_name: str | None = Field(default=None, min_length=1, max_length=100, examples=["Tarun"])
    last_name: str | None = Field(default=None, min_length=1, max_length=100, examples=["Sharma"])
    phone_number: str | None = Field(
        default=None,
        max_length=20,
        examples=["+919876543210"],
        description="Optional contact phone number — not used for authentication",
    )
