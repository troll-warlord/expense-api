import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PaymentMethodCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class PaymentMethodUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)


class PaymentMethodRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    is_default: bool
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID | None
