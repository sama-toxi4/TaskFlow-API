from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "taskflow",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Europe/Moscow",
    enable_utc=True,
)

# Периодическое расписание
celery_app.conf.beat_schedule = {
    "check-due-tasks-every-hour": {
        "task": "app.tasks.send_deadline_reminders",
        "schedule": 3600.0,
    },
}