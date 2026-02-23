import math
from datetime import date as DateType
from decimal import Decimal
from uuid import UUID

import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from structlog.contextvars import bind_contextvars

from app.models.transaction import Transaction
from app.models.user import User
from app.repositories.category import CategoryRepository
from app.repositories.payment_method import PaymentMethodRepository
from app.repositories.transaction import TransactionRepository
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.transaction import (
    CategorySummary,
    TransactionCreate,
    TransactionRead,
    TransactionReadDetail,
    TransactionSummary,
    TransactionUpdate,
)

log = structlog.get_logger(__name__)


class TransactionService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = TransactionRepository(session)
        self._cat_repo = CategoryRepository(session)
        self._pm_repo = PaymentMethodRepository(session)

    async def list_transactions(
        self,
        user: User,
        *,
        page: int = 1,
        page_size: int = 50,
        date_from=None,
        date_to=None,
        category_id=None,
        payment_method_id=None,
        category_type=None,
        q: str | None = None,
    ) -> PaginatedResponse[TransactionRead]:
        offset = (page - 1) * page_size
        filter_kwargs = dict(
            date_from=date_from,
            date_to=date_to,
            category_id=category_id,
            payment_method_id=payment_method_id,
            category_type=category_type,
            q=q,
        )
        transactions = await self._repo.get_all_for_user(user.id, limit=page_size, offset=offset, **filter_kwargs)
        total = await self._repo.count_for_user(user.id, **filter_kwargs)

        return PaginatedResponse(
            data=[TransactionRead.model_validate(t) for t in transactions],
            meta=PaginationMeta(
                total=total,
                page=page,
                page_size=page_size,
                total_pages=math.ceil(total / page_size) if total else 0,
            ),
        )

    async def get_transaction(self, transaction_id: UUID, user: User) -> TransactionReadDetail:
        tx = await self._repo.get_detail(transaction_id, user.id)
        if tx is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found",
            )
        return TransactionReadDetail.model_validate(tx)

    async def create_transaction(self, payload: TransactionCreate, user: User) -> TransactionRead:
        await self._validate_references(payload.category_id, payload.payment_method_id, user.id)

        transaction = Transaction(
            amount=payload.amount,
            date=payload.date,
            category_id=payload.category_id,
            payment_method_id=payload.payment_method_id,
            description=payload.description,
            created_by=user.id,
            updated_by=user.id,
        )
        created = await self._repo.create(transaction)
        # Bind to request context — appears in the single consolidated access line.
        bind_contextvars(transaction_id=str(created.id))
        return TransactionRead.model_validate(created)

    async def update_transaction(self, transaction_id: UUID, payload: TransactionUpdate, user: User) -> TransactionRead:
        tx = await self._repo.get_by_id(transaction_id)
        if tx is None or tx.created_by != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found",
            )

        update_data = payload.model_dump(exclude_unset=True)

        if "category_id" in update_data or "payment_method_id" in update_data:
            await self._validate_references(
                update_data.get("category_id", tx.category_id),
                update_data.get("payment_method_id", tx.payment_method_id),
                user.id,
            )

        update_data["updated_by"] = user.id
        updated = await self._repo.update(tx, update_data)
        bind_contextvars(
            transaction_id=str(transaction_id),
            updated_fields=list(update_data.keys()),
        )
        return TransactionRead.model_validate(updated)

    async def delete_transaction(self, transaction_id: UUID, user: User) -> None:
        tx = await self._repo.get_by_id(transaction_id)
        if tx is None or tx.created_by != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found",
            )
        await self._repo.delete(tx)
        bind_contextvars(transaction_id=str(transaction_id))

    # ------------------------------------------------------------------
    async def get_summary(
        self,
        user: User,
        *,
        date_from: DateType | None = None,
        date_to: DateType | None = None,
    ) -> TransactionSummary:
        rows = await self._repo.get_summary(user.id, date_from=date_from, date_to=date_to)

        by_category = [
            CategorySummary(
                category_id=row["category_id"],
                category_name=row["category_name"],
                category_type=str(row["category_type"].value),
                total=Decimal(str(row["total"])),
                count=row["count"],
            )
            for row in rows
        ]

        total_income = sum((c.total for c in by_category if c.category_type == "income"), Decimal(0))
        total_expense = sum((c.total for c in by_category if c.category_type == "expense"), Decimal(0))

        return TransactionSummary(
            date_from=date_from,
            date_to=date_to,
            total_income=total_income,
            total_expense=total_expense,
            net=total_income - total_expense,
            by_category=by_category,
        )

    async def _validate_references(self, category_id: UUID, payment_method_id: UUID, user_id: UUID) -> None:
        cat = await self._cat_repo.get_user_category(category_id, user_id)
        if cat is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found or not accessible",
            )
        pm = await self._pm_repo.get_user_payment_method(payment_method_id, user_id)
        if pm is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment method not found or not accessible",
            )
