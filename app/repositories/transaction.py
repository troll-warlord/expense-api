from datetime import date as DateType
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models.category import Category, CategoryType
from app.models.payment_method import PaymentMethod
from app.models.transaction import Transaction
from app.repositories.base import BaseRepository


class TransactionRepository(BaseRepository[Transaction]):
    model = Transaction

    def _build_filters(
        self,
        user_id: UUID,
        *,
        date_from: DateType | None = None,
        date_to: DateType | None = None,
        category_id: UUID | None = None,
        payment_method_id: UUID | None = None,
        q: str | None = None,
    ) -> list:
        """Return a list of SQLAlchemy filter clauses."""
        filters = [Transaction.created_by == user_id]
        if date_from:
            filters.append(Transaction.date >= date_from)
        if date_to:
            filters.append(Transaction.date <= date_to)
        if category_id:
            filters.append(Transaction.category_id == category_id)
        if payment_method_id:
            filters.append(Transaction.payment_method_id == payment_method_id)
        if q:
            filters.append(Transaction.description.ilike(f"%{q}%"))
        return filters

    async def get_all_for_user(
        self,
        user_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
        date_from: DateType | None = None,
        date_to: DateType | None = None,
        category_id: UUID | None = None,
        payment_method_id: UUID | None = None,
        category_type: CategoryType | None = None,
        q: str | None = None,
    ) -> list[Transaction]:
        """Return transactions owned by the given user, newest first."""
        filters = self._build_filters(
            user_id,
            date_from=date_from,
            date_to=date_to,
            category_id=category_id,
            payment_method_id=payment_method_id,
            q=q,
        )
        stmt = select(Transaction).where(*filters).order_by(Transaction.date.desc(), Transaction.created_at.desc()).limit(limit).offset(offset)
        if category_type is not None:
            stmt = stmt.join(Category, Transaction.category_id == Category.id).where(Category.type == category_type)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_detail(self, transaction_id: UUID, user_id: UUID) -> Transaction | None:
        """Fetch a single transaction with joined category and payment_method."""
        result = await self._session.execute(
            select(Transaction)
            .where(
                Transaction.id == transaction_id,
                Transaction.created_by == user_id,
            )
            .options(
                selectinload(Transaction.category),
                selectinload(Transaction.payment_method),
            )
        )
        return result.scalar_one_or_none()

    async def count_for_user(
        self,
        user_id: UUID,
        *,
        date_from: DateType | None = None,
        date_to: DateType | None = None,
        category_id: UUID | None = None,
        payment_method_id: UUID | None = None,
        category_type: CategoryType | None = None,
        q: str | None = None,
    ) -> int:
        filters = self._build_filters(
            user_id,
            date_from=date_from,
            date_to=date_to,
            category_id=category_id,
            payment_method_id=payment_method_id,
            q=q,
        )
        stmt = select(func.count()).select_from(Transaction).where(*filters)
        if category_type is not None:
            stmt = stmt.join(Category, Transaction.category_id == Category.id).where(Category.type == category_type)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_export_for_user(
        self,
        user_id: UUID,
        *,
        date_from: DateType | None = None,
        date_to: DateType | None = None,
        category_id: UUID | None = None,
        payment_method_id: UUID | None = None,
        category_type: CategoryType | None = None,
        q: str | None = None,
    ) -> list:
        """Return all matching transactions with joined category/PM names for CSV export."""
        filters = self._build_filters(
            user_id,
            date_from=date_from,
            date_to=date_to,
            category_id=category_id,
            payment_method_id=payment_method_id,
            q=q,
        )
        stmt = (
            select(
                Transaction.id,
                Transaction.date,
                Transaction.description,
                Transaction.amount,
                Transaction.source,
                Category.name.label("category_name"),
                Category.type.label("category_type"),
                PaymentMethod.name.label("payment_method_name"),
            )
            .join(Category, Transaction.category_id == Category.id)
            .join(PaymentMethod, Transaction.payment_method_id == PaymentMethod.id)
            .where(*filters)
            .order_by(Transaction.date.desc(), Transaction.created_at.desc())
        )
        if category_type is not None:
            stmt = stmt.where(Category.type == category_type)
        result = await self._session.execute(stmt)
        return result.mappings().all()

    async def get_summary(
        self,
        user_id: UUID,
        *,
        date_from: DateType | None = None,
        date_to: DateType | None = None,
    ) -> list:
        """Return per-category aggregates for the given user and date range."""
        filters = self._build_filters(user_id, date_from=date_from, date_to=date_to)
        stmt = (
            select(
                Category.id.label("category_id"),
                Category.name.label("category_name"),
                Category.type.label("category_type"),
                func.sum(Transaction.amount).label("total"),
                func.count(Transaction.id).label("count"),
            )
            .join(Category, Transaction.category_id == Category.id)
            .where(*filters)
            .group_by(Category.id, Category.name, Category.type)
            .order_by(Category.type, func.sum(Transaction.amount).desc())
        )
        result = await self._session.execute(stmt)
        return result.mappings().all()
