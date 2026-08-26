import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
import subprocess
import sys
import time
from pathlib import Path

from app.core.celery_app import celery_app
from app.db.session import async_session_maker
from app.models.task import Task

@celery_app.task(name="app.tasks.check_due_dates")
def check_due_dates():
    """Проверяет задачи с дедлайном в ближайшие 24 часа и логирует их."""
    asyncio.run(_check_due_dates_async())

async def _check_due_dates_async():
    now = datetime.now(timezone.utc)
    deadline = now + timedelta(hours=24)
    async with async_session_maker() as session:
        result = await session.execute(
            select(Task).where(Task.due_date.isnot(None),
                               Task.due_date <= deadline,
                               Task.due_date >= now))
        tasks = result.scalars().all()
        for task in tasks:
            # Здесь можно отправить email или другое уведомление
            print(f"Notification: Task '{task.title}' is due at {task.due_date}")

        return f"Found {len(tasks)} tasks due soon"

def start_celery_worker():
    cmd = [
        sys.executable, "-m", "celery",
        "-A", "app.core.celery_app.celery_app",
        "worker",
        "--loglevel=info",
        "--pool=solo"  # обязательно для Windows
    ]
    return subprocess.Popen(cmd, cwd=str(Path(__file__).resolve().parent.parent))

def start_celery_beat():
    cmd = [
        sys.executable, "-m", "celery",
        "-A", "app.core.celery_app.celery_app",
        "beat",
        "--loglevel=info"
    ]
    return subprocess.Popen(cmd, cwd=str(Path(__file__).resolve().parent.parent))

def stop_process(process):
    if process and process.poll() is None:
        process.terminate()
        process.wait(timeout=5)