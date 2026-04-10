from __future__ import annotations

from typing import Generic, TypeVar
from uuid import uuid4

from pydantic import BaseModel, ConfigDict


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    request_id: str
    data: T

    model_config = ConfigDict(arbitrary_types_allowed=True)


def build_response(data: T) -> ApiResponse[T]:
    return ApiResponse[T](request_id=f"req_{uuid4().hex}", data=data)
