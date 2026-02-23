from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("country_code", "phone_number", name="uq_users_country_phone"),)

    # Phone identity (split into country code + local number)
    country_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="E.164 country code, e.g. +91, +1",
    )
    phone_number: Mapped[str] = mapped_column(
        String(15),
        nullable=False,
        index=True,
        comment="Local phone number without country code",
    )

    # Profile fields (filled after OTP verification)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True, unique=True)
    is_profile_complete: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="True once user has submitted first_name, last_name, email",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    @property
    def display_name(self) -> str:
        """Full name if set, first name only if last is missing, otherwise phone."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        if self.first_name:
            return self.first_name
        return f"{self.country_code} {self.phone_number}"

    def __repr__(self) -> str:
        return f"<User id={self.id} phone={self.country_code}{self.phone_number}>"
