from fastapi import FastAPI
from app.api.v1.router import api_router
from app.api.v1.endpoints import health
from app.db.base import Base
from app.models.user import User, ProjectUsers
from app.models.project import Project
from app.models.task import Task, TaskTags
from app.models.tag import Tag

app = FastAPI(title="TaskFlow API", version="0.1.0")
app.include_router(api_router, prefix="/api/v1")
app.include_router(health.router, tags=["health"])
