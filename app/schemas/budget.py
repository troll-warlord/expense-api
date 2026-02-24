import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class BudgetCreate(BaseModel):
    category_id: uuid.UUID | None = Field(
        default=None,
        description="Category to budget for. Omit (null) for an overall spending budget.",
    )
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Monthly limit")
    period: str = Field(default="monthly", pattern="^monthly$")


class BudgetUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    period: str | None = Field(default=None, pattern="^monthly$")


class BudgetCategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: str


class BudgetRead(BaseModel):
    """Budget with live utilization for the current calendar month."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category_id: uuid.UUID | None
    category: BudgetCategoryRead | None
    amount: Decimal
    period: str
    # Utilization — computed at query time, not stored
    spent: Decimal = Field(description="Total expenses this month for this budget's scope")
    percent: float = Field(description="spent / amount * 100, capped at 999")
    remaining: Decimal = Field(description="amount - spent, can be negative if over budget")
    created_at: datetime
    updated_at: datetime
