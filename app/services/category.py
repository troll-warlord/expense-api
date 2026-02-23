from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from structlog.contextvars import bind_contextvars

from app.models.category import Category
from app.models.user import User
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate


class CategoryService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = CategoryRepository(session)

    async def list_categories(self, user: User) -> list[CategoryRead]:
        categories = await self._repo.get_visible_to_user(user.id)
        return [CategoryRead.model_validate(c) for c in categories]

    async def create_category(self, payload: CategoryCreate, user: User) -> CategoryRead:
        category = Category(
            name=payload.name,
            type=payload.type,
            is_default=False,
            created_by=user.id,
            updated_by=user.id,
        )
        created = await self._repo.create(category)
        bind_contextvars(category_id=str(created.id))
        return CategoryRead.model_validate(created)

    async def update_category(self, category_id: UUID, payload: CategoryUpdate, user: User) -> CategoryRead:
        category = await self._repo.get_user_category(category_id, user.id)
        self._ensure_exists_and_owned(category, user.id)

        update_data = payload.model_dump(exclude_unset=True)
        update_data["updated_by"] = user.id
        updated = await self._repo.update(category, update_data)
        bind_contextvars(category_id=str(category_id))
        return CategoryRead.model_validate(updated)

    async def delete_category(self, category_id: UUID, user: User) -> None:
        category = await self._repo.get_user_category(category_id, user.id)
        self._ensure_exists_and_owned(category, user.id)
        try:
            await self._repo.delete(category)
            bind_contextvars(category_id=str(category_id))
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete: this category has existing transactions",
            )

    # ------------------------------------------------------------------
    def _ensure_exists_and_owned(self, category: Category | None, user_id: UUID) -> None:
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )
        if category.is_default:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="System default categories cannot be modified",
            )
        if category.created_by != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify this category",
            )
