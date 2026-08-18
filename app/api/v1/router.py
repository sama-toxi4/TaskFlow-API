from fastapi import APIRouter
from app.api.v1.endpoints import hello, health

api_router = APIRouter()
api_router.include_router(hello.router, tags=["hello"])
api_router.include_router(health.router, tags=["health"])