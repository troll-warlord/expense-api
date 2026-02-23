from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ResponseWrapper(BaseModel, Generic[T]):
    """Standard API response envelope.

    Every endpoint returns this shape:
    {
        "success": true,
        "message": "...",
        "data": <T>
    }
    """

    success: bool
    message: str
    data: T | None = None

    @classmethod
    def ok(cls, data: T | None = None, message: str = "Success") -> "ResponseWrapper[T]":
        return cls(success=True, message=message, data=data)

    @classmethod
    def fail(cls, message: str, data: T | None = None) -> "ResponseWrapper[T]":
        return cls(success=False, message=message, data=data)


class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Success"
    data: list[T]
    meta: PaginationMeta
