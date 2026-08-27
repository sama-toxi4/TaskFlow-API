from fastapi import FastAPI
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.redis import redis_client, delete_cache
from app.tasks import start_celery_worker, start_celery_beat, stop_process


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Очищаем кеш
    await delete_cache("tags:all")

    # Запускаем селери
    worker_process = start_celery_worker()
    beat_process = start_celery_beat()

    yield

    stop_process(worker_process)
    stop_process(beat_process)

    await redis_client.close()

app = FastAPI(title="TaskFlow API", version="0.1.0", lifespan=lifespan)

app.include_router(api_router, prefix="/api/v1")

# Подключаем статические файлы (фронтенд)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/", include_in_schema=False)
async def read_index():
    return FileResponse("frontend/index.html")