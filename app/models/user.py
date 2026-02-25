from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    # Primary auth identifier — always present
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Login identifier; verified via OTP at registration",
    )

    # Optional contact / legacy fields
    country_code: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        comment="E.164 country code, e.g. +91, +1 — contact info only, not used for auth",
    )
    phone_number: Mapped[str | None] = mapped_column(
        String(15),
        nullable=True,
        index=True,
        comment="Local phone number without country code — contact info only, not used for auth",
    )

    # Profile fields (filled after OTP verification)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_profile_complete: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="True once user has submitted first_name and last_name",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    @property
    def display_name(self) -> str:
        """Full name if set, first name only if last is missing, otherwise email."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        if self.first_name:
            return self.first_name
        return self.email

    def __repr__(self) -> str:
        return f"<User id={self.id} phone={self.country_code}{self.phone_number}>"
