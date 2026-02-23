from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import CurrentUser, DBSession
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.schemas.common import ResponseWrapper
from app.services.category import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])


def _category_service(db: DBSession) -> CategoryService:
    return CategoryService(db)


CategoryServiceDep = Depends(_category_service)


@router.get("", response_model=ResponseWrapper[list[CategoryRead]], status_code=status.HTTP_200_OK)
async def list_categories(current_user: CurrentUser, service: CategoryService = CategoryServiceDep):
    data = await service.list_categories(current_user)
    return ResponseWrapper.ok(data=data)


@router.post("", response_model=ResponseWrapper[CategoryRead], status_code=status.HTTP_201_CREATED)
async def create_category(payload: CategoryCreate, current_user: CurrentUser, service: CategoryService = CategoryServiceDep):
    data = await service.create_category(payload, current_user)
    return ResponseWrapper.ok(data=data, message="Category created")


@router.patch("/{category_id}", response_model=ResponseWrapper[CategoryRead], status_code=status.HTTP_200_OK)
async def update_category(category_id: UUID, payload: CategoryUpdate, current_user: CurrentUser, service: CategoryService = CategoryServiceDep):
    data = await service.update_category(category_id, payload, current_user)
    return ResponseWrapper.ok(data=data, message="Category updated")


@router.delete("/{category_id}", response_model=ResponseWrapper[None], status_code=status.HTTP_200_OK)
async def delete_category(category_id: UUID, current_user: CurrentUser, service: CategoryService = CategoryServiceDep):
    await service.delete_category(category_id, current_user)
    return ResponseWrapper.ok(message="Category deleted")
