import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Root declarative base for all SQLAlchemy ORM models."""

    pass


class TimestampMixin:
    """created_at / updated_at — sorted to the end of every table."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        sort_order=1000,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
        sort_order=1001,
    )


class AuditMixin:
    """source / created_by / updated_by — sorted after timestamps."""

    source: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None,
        comment="Request origin: web, android, ios, api.",
        sort_order=999,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        sort_order=1002,
    )
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None,
        sort_order=1003,
    )


class BaseModel(Base, TimestampMixin, AuditMixin):
    """Abstract base for all domain tables.

    Column order in every table:
      id  |  <domain columns>  |  source  created_at  updated_at  created_by  updated_by
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        sort_order=-1,  # always first
    )
