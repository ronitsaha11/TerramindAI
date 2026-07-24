from typing import Any, Dict, Generic, Optional, TypeVar
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")

class ErrorDetail(BaseModel):
    code: str
    message: str
    trace_id: str

class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred.",
                    "trace_id": "req-12345"
                }
            }
        }
    )

class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
