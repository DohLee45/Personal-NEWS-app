"""GET /api/usage — OpenRouter 일일 사용량 조회"""

from fastapi import APIRouter
from services.usage_tracker import get_usage_status

router = APIRouter()


@router.get("/usage")
async def get_usage() -> dict:
    return get_usage_status()
