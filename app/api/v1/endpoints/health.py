from app.schemas.health import HealthResponse
from fastapi import APIRouter

router = APIRouter()

@router.get("/health", tags=["health"], response_model=HealthResponse)
async def health_check() -> dict:
    return {"status": "ok"}