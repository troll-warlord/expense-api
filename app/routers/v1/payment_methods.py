from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.dependencies import CurrentUser, DBSession
from app.schemas.common import ResponseWrapper
from app.schemas.payment_method import (
    PaymentMethodCreate,
    PaymentMethodRead,
    PaymentMethodUpdate,
)
from app.services.payment_method import PaymentMethodService

router = APIRouter(prefix="/payment-methods", tags=["Payment Methods"])


def _payment_method_service(db: DBSession) -> PaymentMethodService:
    return PaymentMethodService(db)


PaymentMethodServiceDep = Depends(_payment_method_service)


@router.get("", response_model=ResponseWrapper[list[PaymentMethodRead]], status_code=status.HTTP_200_OK)
async def list_payment_methods(current_user: CurrentUser, service: PaymentMethodService = PaymentMethodServiceDep):
    data = await service.list_payment_methods(current_user)
    return ResponseWrapper.ok(data=data)


@router.post("", response_model=ResponseWrapper[PaymentMethodRead], status_code=status.HTTP_201_CREATED)
async def create_payment_method(payload: PaymentMethodCreate, current_user: CurrentUser, service: PaymentMethodService = PaymentMethodServiceDep):
    data = await service.create_payment_method(payload, current_user)
    return ResponseWrapper.ok(data=data, message="Payment method created")


@router.patch("/{method_id}", response_model=ResponseWrapper[PaymentMethodRead], status_code=status.HTTP_200_OK)
async def update_payment_method(method_id: UUID, payload: PaymentMethodUpdate, current_user: CurrentUser, service: PaymentMethodService = PaymentMethodServiceDep):
    data = await service.update_payment_method(method_id, payload, current_user)
    return ResponseWrapper.ok(data=data, message="Payment method updated")


@router.delete("/{method_id}", response_model=ResponseWrapper[None], status_code=status.HTTP_200_OK)
async def delete_payment_method(method_id: UUID, current_user: CurrentUser, service: PaymentMethodService = PaymentMethodServiceDep):
    await service.delete_payment_method(method_id, current_user)
    return ResponseWrapper.ok(message="Payment method deleted")
