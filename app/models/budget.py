import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Budget(BaseModel):
    """Monthly spending budget — per-category or overall.

    Scoping rules
    -------------
    - category_id = NULL  → overall spending budget (all expense categories summed).
    - category_id = <id>  → budget for that specific category only.
    - Uniqueness enforced by two partial unique indexes in the migration:
        uq_budgets_user_overall   (created_by, period) WHERE category_id IS NULL
        uq_budgets_user_category  (created_by, category_id, period) WHERE category_id IS NOT NULL
    """

    __tablename__ = "budgets"
    __table_args__ = (CheckConstraint("amount > 0", name="ck_budgets_amount_positive"),)

    category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2),
        nullable=False,
    )
    period: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="monthly",
        comment="Recurrence period: monthly (only supported value for now)",
    )

    # Override AuditMixin.created_by to add index — every budget query filters by user
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        default=None,
        index=True,
        sort_order=1002,
    )

    category: Mapped["Category | None"] = relationship(  # noqa: F821
        "Category",
        lazy="raise",
        foreign_keys=[category_id],
    )

    def __repr__(self) -> str:
        return f"<Budget id={self.id} category_id={self.category_id} amount={self.amount}>"
