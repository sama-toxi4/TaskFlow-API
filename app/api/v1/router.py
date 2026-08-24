from fastapi import APIRouter
from app.api.v1.endpoints import db_check, users, auth, projects

api_router = APIRouter()

api_router.include_router(db_check.router, tags=["db-check"])
api_router.include_router(users.router, tags=["users"])
api_router.include_router(auth.router, tags=["auth"], prefix="/auth")
api_router.include_router(projects.router, tags=["project"], prefix="/projects")
