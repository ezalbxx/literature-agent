"""共享 Pydantic 模型"""

from pydantic import BaseModel
from typing import Optional


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    llm_provider: str
