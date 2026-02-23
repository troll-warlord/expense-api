import uuid
from datetime import date as DateType
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.category import CategoryRead
from app.schemas.payment_method import PaymentMethodRead


class TransactionCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    date: DateType
    category_id: uuid.UUID
    payment_method_id: uuid.UUID
    description: str | None = Field(default=None, max_length=1000)


class TransactionUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    date: DateType | None = None
    category_id: uuid.UUID | None = None
    payment_method_id: uuid.UUID | None = None
    description: str | None = Field(default=None, max_length=1000)


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    # 'created_by' on the model is exposed as 'user_id' to clients
    user_id: uuid.UUID | None = Field(default=None, validation_alias="created_by")
    amount: Decimal
    date: DateType
    description: str | None
    category_id: uuid.UUID
    payment_method_id: uuid.UUID
    source: str | None
    created_at: datetime
    updated_at: datetime


class TransactionReadDetail(TransactionRead):
    """Extended read schema that includes joined relations."""

    category: CategoryRead
    payment_method: PaymentMethodRead


class CategorySummary(BaseModel):
    category_id: uuid.UUID
    category_name: str
    category_type: str  # "income" | "expense"
    total: Decimal
    count: int


class TransactionSummary(BaseModel):
    """Aggregated spending/income summary for a user."""

    date_from: DateType | None = None
    date_to: DateType | None = None
    total_income: Decimal
    total_expense: Decimal
    net: Decimal  # total_income - total_expense
    by_category: list[CategorySummary]
