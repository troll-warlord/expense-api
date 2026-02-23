import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Transaction(BaseModel):
    __tablename__ = "transactions"
    __table_args__ = (CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),)

    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=12, scale=2),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    payment_method_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("payment_methods.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Override AuditMixin.created_by to add an index — this column is used in
    # every transaction query (WHERE created_by = :user_id) so it must be indexed.
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        index=True,
        sort_order=1002,
    )

    # Relationships (lazy="raise" keeps queries explicit)
    category: Mapped["Category"] = relationship(  # noqa: F821
        "Category",
        lazy="raise",
        foreign_keys=[category_id],
    )
    payment_method: Mapped["PaymentMethod"] = relationship(  # noqa: F821
        "PaymentMethod",
        lazy="raise",
        foreign_keys=[payment_method_id],
    )

    def __repr__(self) -> str:
        return f"<Transaction id={self.id} amount={self.amount} date={self.date}>"
