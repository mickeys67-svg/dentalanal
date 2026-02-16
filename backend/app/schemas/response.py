from typing import Generic, TypeVar, Optional, Any, Dict
from pydantic import BaseModel
from enum import Enum

T = TypeVar('T')

class ResponseStatus(str, Enum):
    SUCCESS = "success"
    FAIL = "fail"   # For expected failures (e.g. validation error)
    ERROR = "error" # For unexpected exceptions

class APIResponse(BaseModel, Generic[T]):
    """
    Standard API Response Envelope
    Follows Google AIP & JSON:API trends for consistent data exchange.
    """
    status: ResponseStatus
    data: Optional[T] = None
    message: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None # Metadata execution time, version, pagination, etc.

    class Config:
        from_attributes = True
