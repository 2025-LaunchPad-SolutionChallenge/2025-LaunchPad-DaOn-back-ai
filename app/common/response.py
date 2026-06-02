from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: T | None = None

    @classmethod
    def ok(cls, data: T | None = None, message: str = "success") -> "ApiResponse[T]":
        return cls(code=200, message=message, data=data)

    @classmethod
    def created(cls, data: T | None = None, message: str = "created") -> "ApiResponse[T]":
        return cls(code=201, message=message, data=data)
