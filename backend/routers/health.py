"""健康检查路由"""

from fastapi import APIRouter

from config import APP_NAME, APP_VERSION, LLM_PROVIDER
from backend.models.common import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/api/health", response_model=HealthResponse)
def health_check():
    """后端健康检查"""
    return HealthResponse(
        status="ok",
        version=APP_VERSION,
        llm_provider=LLM_PROVIDER,
    )
