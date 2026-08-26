from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "taskflow",
    broker=settings.redis_url,       # URL Redis для брокера
    backend=settings.redis_url,      # URL Redis для результатов
    include=["app.tasks"]            # модуль с задачами
)

celery_app.conf.beat_schedule = {
    "check-due-dates-every-hour": {
        "task": "app.tasks.check_due_dates",
        "schedule": 3600.0,
    },
}
celery_app.conf.timezone = "UTC"