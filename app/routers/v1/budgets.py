from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import CurrentUser, DBSession
from app.schemas.budget import BudgetCreate, BudgetRead, BudgetUpdate
from app.schemas.common import ResponseWrapper
from app.services.budget import BudgetService

router = APIRouter(prefix="/budgets", tags=["Budgets"])


def _budget_service(db: DBSession) -> BudgetService:
    return BudgetService(db)


BudgetServiceDep = Depends(_budget_service)


@router.get("", response_model=ResponseWrapper[list[BudgetRead]], status_code=status.HTTP_200_OK)
async def list_budgets(current_user: CurrentUser, service: BudgetService = BudgetServiceDep):
    data = await service.list_budgets(current_user)
    return ResponseWrapper.ok(data=data)


@router.post("", response_model=ResponseWrapper[BudgetRead], status_code=status.HTTP_201_CREATED)
async def create_budget(
    payload: BudgetCreate, current_user: CurrentUser, service: BudgetService = BudgetServiceDep
):
    data = await service.create_budget(payload, current_user)
    return ResponseWrapper.ok(data=data, message="Budget created")


@router.patch(
    "/{budget_id}", response_model=ResponseWrapper[BudgetRead], status_code=status.HTTP_200_OK
)
async def update_budget(
    budget_id: UUID,
    payload: BudgetUpdate,
    current_user: CurrentUser,
    service: BudgetService = BudgetServiceDep,
):
    data = await service.update_budget(budget_id, payload, current_user)
    return ResponseWrapper.ok(data=data, message="Budget updated")


@router.delete(
    "/{budget_id}", response_model=ResponseWrapper[None], status_code=status.HTTP_200_OK
)
async def delete_budget(
    budget_id: UUID, current_user: CurrentUser, service: BudgetService = BudgetServiceDep
):
    await service.delete_budget(budget_id, current_user)
    return ResponseWrapper.ok(message="Budget deleted")
