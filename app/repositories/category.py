from uuid import UUID

from sqlalchemy import or_, select

from app.models.category import Category
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    model = Category

    async def get_visible_to_user(
        self,
        user_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Category]:
        """Return system defaults + the calling user's custom categories."""
        result = await self._session.execute(
            select(Category)
            .where(
                or_(
                    Category.is_default.is_(True),
                    (Category.is_default.is_(False)) & (Category.created_by == user_id),
                )
            )
            .order_by(Category.is_default.desc(), Category.name)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_user_category(self, category_id: UUID, user_id: UUID) -> Category | None:
        """Fetch a category only if it's a default or owned by the user."""
        result = await self._session.execute(
            select(Category).where(
                Category.id == category_id,
                or_(
                    Category.is_default.is_(True),
                    (Category.is_default.is_(False)) & (Category.created_by == user_id),
                ),
            )
        )
        return result.scalar_one_or_none()
