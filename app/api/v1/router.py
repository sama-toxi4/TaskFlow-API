from fastapi import APIRouter
from app.api.v1.endpoints import hello, db_check, users, auth

api_router = APIRouter()
api_router.include_router(hello.router, tags=["hello"])
api_router.include_router(db_check.router, tags=["db-check"])
api_router.include_router(users.router, tags=["users"])
api_router.include_router(auth.router, tags=["auth"])
