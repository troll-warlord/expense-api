from datetime import date as DateType
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse

from app.core.dependencies import ClientSource, CurrentUser, DBSession
from app.models.category import CategoryType
from app.schemas.common import PaginatedResponse, ResponseWrapper
from app.schemas.transaction import (
    TransactionCreate,
    TransactionRead,
    TransactionReadDetail,
    TransactionSummary,
    TransactionUpdate,
)
from app.services.transaction import TransactionService

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def _transaction_service(db: DBSession) -> TransactionService:
    return TransactionService(db)


TransactionServiceDep = Depends(_transaction_service)


@router.get("", response_model=PaginatedResponse[TransactionRead], status_code=status.HTTP_200_OK)
async def list_transactions(
    current_user: CurrentUser,
    service: TransactionService = TransactionServiceDep,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=1000),
    date_from: DateType | None = Query(default=None, description="Filter on or after this date (YYYY-MM-DD)"),
    date_to: DateType | None = Query(default=None, description="Filter on or before this date (YYYY-MM-DD)"),
    category_id: UUID | None = Query(default=None, description="Filter by category UUID"),
    payment_method_id: UUID | None = Query(default=None, description="Filter by payment method UUID"),
    type: CategoryType | None = Query(default=None, description="Filter by transaction type: income | expense"),
    q: str | None = Query(default=None, max_length=200, description="Search description (case-insensitive substring)"),
):
    return await service.list_transactions(
        current_user,
        page=page,
        page_size=page_size,
        date_from=date_from,
        date_to=date_to,
        category_id=category_id,
        payment_method_id=payment_method_id,
        category_type=type,
        q=q,
    )


@router.get(
    "/summary",
    response_model=ResponseWrapper[TransactionSummary],
    status_code=status.HTTP_200_OK,
    summary="Spending summary",
    description="Returns income/expense totals and a per-category breakdown. Supports the same date range filters as the transaction list.",
)
async def get_summary(
    current_user: CurrentUser,
    service: TransactionService = TransactionServiceDep,
    date_from: DateType | None = Query(default=None, description="Start of date range (YYYY-MM-DD)"),
    date_to: DateType | None = Query(default=None, description="End of date range (YYYY-MM-DD)"),
):
    data = await service.get_summary(current_user, date_from=date_from, date_to=date_to)
    return ResponseWrapper.ok(data=data)


@router.get(
    "/export",
    summary="Export transactions as CSV",
    description="Streams a CSV file of all transactions matching the given filters. No row limit.",
    status_code=status.HTTP_200_OK,
)
async def export_transactions(
    current_user: CurrentUser,
    service: TransactionService = TransactionServiceDep,
    date_from: DateType | None = Query(default=None),
    date_to: DateType | None = Query(default=None),
    category_id: UUID | None = Query(default=None),
    payment_method_id: UUID | None = Query(default=None),
    type: CategoryType | None = Query(default=None),
    q: str | None = Query(default=None, max_length=200),
):
    csv_content, _ = await service.export_csv(
        current_user,
        date_from=date_from,
        date_to=date_to,
        category_id=category_id,
        payment_method_id=payment_method_id,
        category_type=type,
        q=q,
    )
    filename = f"transactions-{datetime.today().strftime('%Y-%m-%d')}.csv"
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{transaction_id}", response_model=ResponseWrapper[TransactionReadDetail], status_code=status.HTTP_200_OK)
async def get_transaction(transaction_id: UUID, current_user: CurrentUser, service: TransactionService = TransactionServiceDep):
    data = await service.get_transaction(transaction_id, current_user)
    return ResponseWrapper.ok(data=data)


@router.post("", response_model=ResponseWrapper[TransactionRead], status_code=status.HTTP_201_CREATED)
async def create_transaction(payload: TransactionCreate, current_user: CurrentUser, source: ClientSource, service: TransactionService = TransactionServiceDep):
    data = await service.create_transaction(payload, current_user, source=source)
    return ResponseWrapper.ok(data=data, message="Transaction created")


@router.patch("/{transaction_id}", response_model=ResponseWrapper[TransactionRead], status_code=status.HTTP_200_OK)
async def update_transaction(transaction_id: UUID, payload: TransactionUpdate, current_user: CurrentUser, service: TransactionService = TransactionServiceDep):
    data = await service.update_transaction(transaction_id, payload, current_user)
    return ResponseWrapper.ok(data=data, message="Transaction updated")


@router.delete("/{transaction_id}", response_model=ResponseWrapper[None], status_code=status.HTTP_200_OK)
async def delete_transaction(transaction_id: UUID, current_user: CurrentUser, service: TransactionService = TransactionServiceDep):
    await service.delete_transaction(transaction_id, current_user)
    return ResponseWrapper.ok(message="Transaction deleted")
