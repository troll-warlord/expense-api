from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from structlog.contextvars import bind_contextvars

from app.models.payment_method import PaymentMethod
from app.models.user import User
from app.repositories.payment_method import PaymentMethodRepository
from app.schemas.payment_method import (
    PaymentMethodCreate,
    PaymentMethodRead,
    PaymentMethodUpdate,
)


class PaymentMethodService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = PaymentMethodRepository(session)

    async def list_payment_methods(self, user: User) -> list[PaymentMethodRead]:
        methods = await self._repo.get_visible_to_user(user.id)
        return [PaymentMethodRead.model_validate(m) for m in methods]

    async def create_payment_method(self, payload: PaymentMethodCreate, user: User) -> PaymentMethodRead:
        method = PaymentMethod(
            name=payload.name,
            is_default=False,
            created_by=user.id,
            updated_by=user.id,
        )
        created = await self._repo.create(method)
        bind_contextvars(payment_method_id=str(created.id))
        return PaymentMethodRead.model_validate(created)

    async def update_payment_method(self, method_id: UUID, payload: PaymentMethodUpdate, user: User) -> PaymentMethodRead:
        method = await self._repo.get_user_payment_method(method_id, user.id)
        self._ensure_exists_and_owned(method, user.id)

        update_data = payload.model_dump(exclude_unset=True)
        update_data["updated_by"] = user.id
        updated = await self._repo.update(method, update_data)
        bind_contextvars(payment_method_id=str(method_id))
        return PaymentMethodRead.model_validate(updated)

    async def delete_payment_method(self, method_id: UUID, user: User) -> None:
        method = await self._repo.get_user_payment_method(method_id, user.id)
        self._ensure_exists_and_owned(method, user.id)
        try:
            await self._repo.delete(method)
            bind_contextvars(payment_method_id=str(method_id))
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete: this payment method has existing transactions",
            )

    # ------------------------------------------------------------------
    def _ensure_exists_and_owned(self, method: PaymentMethod | None, user_id: UUID) -> None:
        if method is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment method not found",
            )
        if method.is_default:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="System default payment methods cannot be modified",
            )
        if method.created_by != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify this payment method",
            )
