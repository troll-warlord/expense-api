from uuid import UUID

from sqlalchemy import or_, select

from app.models.payment_method import PaymentMethod
from app.repositories.base import BaseRepository


class PaymentMethodRepository(BaseRepository[PaymentMethod]):
    model = PaymentMethod

    async def get_visible_to_user(
        self,
        user_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PaymentMethod]:
        """Return system defaults + the calling user's custom payment methods."""
        result = await self._session.execute(
            select(PaymentMethod)
            .where(
                or_(
                    PaymentMethod.is_default.is_(True),
                    (PaymentMethod.is_default.is_(False)) & (PaymentMethod.created_by == user_id),
                )
            )
            .order_by(PaymentMethod.is_default.desc(), PaymentMethod.name)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_user_payment_method(self, payment_method_id: UUID, user_id: UUID) -> PaymentMethod | None:
        result = await self._session.execute(
            select(PaymentMethod).where(
                PaymentMethod.id == payment_method_id,
                or_(
                    PaymentMethod.is_default.is_(True),
                    (PaymentMethod.is_default.is_(False)) & (PaymentMethod.created_by == user_id),
                ),
            )
        )
        return result.scalar_one_or_none()
