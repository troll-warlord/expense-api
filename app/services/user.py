import structlog
from sqlalchemy import delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.payment_method import PaymentMethod
from app.models.transaction import Transaction
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserProfileUpdate, UserRead

log = structlog.get_logger(__name__)


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = UserRepository(session)

    async def get_me(self, user: User) -> UserRead:
        return UserRead.model_validate(user)

    async def update_profile(self, user: User, data: UserProfileUpdate) -> UserRead:
        # Only update fields that were explicitly provided
        updates: dict = {"is_profile_complete": True}
        if data.first_name is not None:
            updates["first_name"] = data.first_name
        if data.last_name is not None:
            updates["last_name"] = data.last_name
        if data.email is not None:
            updates["email"] = data.email
        updated = await self._repo.update(user, updates)
        log.info("Profile updated", user_id=str(user.id))
        return UserRead.model_validate(updated)

    async def delete_account(self, user: User) -> None:
        """Permanently delete the account and all user-owned data."""
        uid = user.id
        # Delete in dependency order to avoid FK violations.
        # refresh_tokens cascade automatically via DB FK ON DELETE CASCADE.
        await self._session.execute(sql_delete(Transaction).where(Transaction.created_by == uid))
        await self._session.execute(
            sql_delete(Category).where(Category.created_by == uid, Category.is_default.is_(False))
        )
        await self._session.execute(
            sql_delete(PaymentMethod).where(PaymentMethod.created_by == uid, PaymentMethod.is_default.is_(False))
        )
        await self._repo.delete(user)
        log.warning("Account permanently deleted", user_id=str(uid))
