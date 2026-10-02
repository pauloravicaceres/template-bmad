from typing import Optional, Dict, Any
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Canonical RFC 7807 structured error response."""
    error_code: str
    detail: str
    timestamp: str
    path: str
    metadata: Optional[Dict[str, Any]] = None
