from fastapi import FastAPI
from app.api.v1.router import api_router
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.db.base import Base
from app.models.user import User, ProjectUsers
from app.models.project import Project
from app.models.task import Task, TaskTags
from app.models.tag import Tag

app = FastAPI(title="TaskFlow API", version="0.1.0")

app.include_router(api_router, prefix="/api/v1")

# Подключаем статические файлы (фронтенд)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", include_in_schema=False)
async def read_index():
    return FileResponse("frontend/index.html")