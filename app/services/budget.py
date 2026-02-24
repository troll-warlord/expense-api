from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from structlog.contextvars import bind_contextvars

from app.models.budget import Budget
from app.models.category import Category, CategoryType
from app.models.transaction import Transaction
from app.models.user import User
from app.repositories.budget import BudgetRepository
from app.schemas.budget import BudgetCreate, BudgetRead, BudgetUpdate


class BudgetService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = BudgetRepository(session)
        self._session = session

    # ── Public API ────────────────────────────────────────────────────────────

    async def list_budgets(self, user: User) -> list[BudgetRead]:
        budgets = await self._repo.get_user_budgets(user.id)
        # Eagerly resolve category relationships without N+1
        budgets = await self._load_categories(budgets)
        spent_map = await self._monthly_spent_map(user.id)
        return [self._to_read(b, spent_map) for b in budgets]

    async def create_budget(self, payload: BudgetCreate, user: User) -> BudgetRead:
        # Validate category belongs to user (or is a system category)
        if payload.category_id is not None:
            await self._validate_category(payload.category_id, user.id)

        # Enforce uniqueness
        existing = await self._repo.get_by_category(user.id, payload.category_id, payload.period)
        if existing:
            label = "overall spending" if payload.category_id is None else "that category"
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A {payload.period} budget for {label} already exists",
            )

        budget = Budget(
            category_id=payload.category_id,
            amount=payload.amount,
            period=payload.period,
            created_by=user.id,
            updated_by=user.id,
        )
        created = await self._repo.create(budget)
        bind_contextvars(budget_id=str(created.id))

        budgets = await self._load_categories([created])
        spent_map = await self._monthly_spent_map(user.id)
        return self._to_read(budgets[0], spent_map)

    async def update_budget(self, budget_id: UUID, payload: BudgetUpdate, user: User) -> BudgetRead:
        budget = await self._repo.get_user_budget(budget_id, user.id)
        if budget is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")

        update_data = payload.model_dump(exclude_unset=True)
        update_data["updated_by"] = user.id
        updated = await self._repo.update(budget, update_data)
        bind_contextvars(budget_id=str(budget_id))

        budgets = await self._load_categories([updated])
        spent_map = await self._monthly_spent_map(user.id)
        return self._to_read(budgets[0], spent_map)

    async def delete_budget(self, budget_id: UUID, user: User) -> None:
        budget = await self._repo.get_user_budget(budget_id, user.id)
        if budget is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
        await self._repo.delete(budget)
        bind_contextvars(budget_id=str(budget_id))

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def _load_categories(self, budgets: list[Budget]) -> list[Budget]:
        """Resolve category for each budget in a single query."""
        cat_ids = {b.category_id for b in budgets if b.category_id is not None}
        if not cat_ids:
            return budgets

        result = await self._session.execute(
            select(Category).where(Category.id.in_(cat_ids))
        )
        cats = {c.id: c for c in result.scalars().all()}
        for b in budgets:
            if b.category_id is not None:
                # Inject the already-loaded object to satisfy lazy="raise"
                b.__dict__["category"] = cats.get(b.category_id)
        return budgets

    async def _monthly_spent_map(self, user_id: UUID) -> dict[UUID | None, Decimal]:
        """Return a mapping {category_id → total_expense_this_month} for the user.

        Also includes a None key = sum of ALL expense categories (for overall budget).
        """
        today = date.today()
        first_of_month = today.replace(day=1)

        stmt = (
            select(Transaction.category_id, func.sum(Transaction.amount).label("total"))
            .join(Category, Transaction.category_id == Category.id)
            .where(
                Transaction.created_by == user_id,
                Transaction.date >= first_of_month,
                Transaction.date <= today,
                Category.type == CategoryType.expense,
            )
            .group_by(Transaction.category_id)
        )
        result = await self._session.execute(stmt)
        rows = result.all()

        per_category: dict[UUID | None, Decimal] = {
            row.category_id: Decimal(str(row.total)) for row in rows
        }
        overall = sum(per_category.values(), Decimal("0"))
        per_category[None] = overall
        return per_category

    def _to_read(self, budget: Budget, spent_map: dict[UUID | None, Decimal]) -> BudgetRead:
        spent = spent_map.get(budget.category_id, Decimal("0"))
        remaining = budget.amount - spent
        percent = min(float(spent / budget.amount * 100), 999.0) if budget.amount else 0.0
        cat = budget.__dict__.get("category")  # injected by _load_categories
        return BudgetRead(
            id=budget.id,
            category_id=budget.category_id,
            category=cat,
            amount=budget.amount,
            period=budget.period,
            spent=spent,
            percent=round(percent, 1),
            remaining=remaining,
            created_at=budget.created_at,
            updated_at=budget.updated_at,
        )

    async def _validate_category(self, category_id: UUID, user_id: UUID) -> None:
        """Ensure the category exists and is visible to the user."""
        from sqlalchemy import or_

        result = await self._session.execute(
            select(Category).where(
                Category.id == category_id,
                or_(
                    Category.is_default.is_(True),
                    Category.created_by == user_id,
                ),
            )
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found",
            )
