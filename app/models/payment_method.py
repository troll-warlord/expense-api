from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class PaymentMethod(BaseModel):
    """Payment method (Cash, UPI, Credit Card, etc.).

    Scoping rules
    -------------
    - is_default=True  → system-provided, visible to all users.
    - is_default=False → custom, scoped to the owning user (created_by).
    """

    __tablename__ = "payment_methods"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="True = system default visible to all users",
    )

    def __repr__(self) -> str:
        return f"<PaymentMethod id={self.id} name={self.name}>"
