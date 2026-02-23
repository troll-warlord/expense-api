import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserProfileUpdate, UserRead

log = structlog.get_logger(__name__)


class UserService:
    def __init__(self, session: AsyncSession) -> None:
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

    async def deactivate(self, user: User) -> UserRead:
        updated = await self._repo.update(user, {"is_active": False})
        log.warning("Account deactivated", user_id=str(user.id))
        return UserRead.model_validate(updated)
