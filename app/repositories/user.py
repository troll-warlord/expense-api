from sqlalchemy import select

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_phone(self, country_code: str, phone_number: str) -> User | None:
        result = await self._session.execute(
            select(User).where(
                User.country_code == country_code,
                User.phone_number == phone_number,
            )
        )
        return result.scalar_one_or_none()
