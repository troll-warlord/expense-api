from uuid import UUID

from sqlalchemy import select

from app.models.budget import Budget
from app.repositories.base import BaseRepository


class BudgetRepository(BaseRepository[Budget]):
    model = Budget

    async def get_user_budgets(self, user_id: UUID) -> list[Budget]:
        """Return all budgets owned by the user, ordered by overall-first then category name."""
        result = await self._session.execute(
            select(Budget)
            .where(Budget.created_by == user_id)
            .order_by(Budget.category_id.nulls_first(), Budget.created_at)
        )
        return list(result.scalars().all())

    async def get_user_budget(self, budget_id: UUID, user_id: UUID) -> Budget | None:
        result = await self._session.execute(
            select(Budget).where(Budget.id == budget_id, Budget.created_by == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_category(
        self, user_id: UUID, category_id: UUID | None, period: str
    ) -> Budget | None:
        """Check for an existing budget for the same (user, category, period) triple."""
        if category_id is None:
            stmt = select(Budget).where(
                Budget.created_by == user_id,
                Budget.category_id.is_(None),
                Budget.period == period,
            )
        else:
            stmt = select(Budget).where(
                Budget.created_by == user_id,
                Budget.category_id == category_id,
                Budget.period == period,
            )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
