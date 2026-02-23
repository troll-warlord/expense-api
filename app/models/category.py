import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class CategoryType(str, enum.Enum):
    income = "income"
    expense = "expense"


class Category(BaseModel):
    """Expense / income category.

    Scoping rules
    -------------
    - is_default=True  → visible to ALL users (system-provided rows).
    - is_default=False → scoped by created_by; only the owning user sees them.
    """

    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[CategoryType] = mapped_column(
        Enum(CategoryType, name="category_type", create_type=False),
        nullable=False,
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="True = system default visible to all users",
    )

    def __repr__(self) -> str:
        return f"<Category id={self.id} name={self.name} type={self.type}>"
