from fastapi import APIRouter
from app.api.v1.endpoints import db_check, users, auth, projects, tags, tasks

api_router = APIRouter()

api_router.include_router(db_check.router, tags=["db-check"], prefix="/db_check")
api_router.include_router(users.router, tags=["users"], prefix="/users")
api_router.include_router(auth.router, tags=["auth"], prefix="/auth")
api_router.include_router(projects.router, tags=["project"], prefix="/projects")
api_router.include_router(tags.router, tags=["tags"], prefix="/tags")
api_router.include_router(tasks.router, tags=["tasks"])
