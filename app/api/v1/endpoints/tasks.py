from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_current_user
from app.db.session import get_session
from app.models.project import Project
from app.models.tag import Tag
from app.models.task import Task, TaskTags
from app.models.user import User, ProjectUsers
from app.schemas.project import PageResponse
from app.schemas.task import TaskResponse, TaskCreate
from sqlalchemy import select, or_

router = APIRouter()

#CREATE
@router.post("/projects/{project_id}/tasks", response_model=TaskResponse, status_code=201)
async def create_task(project_id: int,
                      task_data: TaskCreate,
                      db: AsyncSession = Depends(get_session),
                      current_user: User = Depends(get_current_user)):
    # Проверяем доступ к проекту
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    # Проверяем, что пользователь владелец или участник
    if project.owner_id != current_user.id:

        result = await db.execute(select(ProjectUsers).where(ProjectUsers.user_id == current_user.id))
        if not result.scalar_one_or_none():
            raise HTTPException(403, "Not enough permissions")

    # Если назначен исполнитель, проверяем что он участник проекта
    if task_data.assignee_id:
        if task_data.owner_id != current_user.id:

            result = await db.execute(select(ProjectUsers).where(ProjectUsers.user_id == task_data.assignee_id))
            if not result.scalar_one_or_none():
                raise HTTPException(403, "Not enough permissions")

    # Создаём задачу
    new_task = Task(title=task_data.title,
                    description=task_data.description,
                    status=task_data.status,
                    priority=task_data.priority,
                    due_date=task_data.due_date,
                    project_id=project_id,
                    assignee_id=task_data.assignee_id)

    db.add(new_task)

    await db.flush()

    # Добавляем теги
    if task_data.tag_ids:
        for tag_id in task_data.tag_ids:

            # проверить что тег существует
            tag = await db.get(Tag, tag_id)

            if not tag:
                raise HTTPException(404, f"Tag {tag_id} not found")

            db.add(TaskTags(task_id=new_task.id, tag_id=tag_id))

    await db.commit()
    await db.refresh(new_task)

    return new_task

# READ
@router.get("/", response_model=PageResponse[TaskResponse])
async def list_tasks(page: int = Query(1, ge=1),
                     per_page: int = Query(10, ge=1, le=100),
                     priority: str | None = None,
                     project_id: int | None = None,
                     assignee_id: int | None = None,
                     due_before: datetime | None = None,
                     due_after: datetime | None = None,
                     db: AsyncSession = Depends(get_session),
                     current_user: User = Depends(get_current_user)):
    query = select(Task)
    conditions = []

    if current_user.role != "admin":
        # Получаем подзапрос доступных project_id
        accessible_projects = (select(Project.id)
                               .where(or_(Project.owner_id == current_user.id,
                                          Project.id.in_(select(ProjectUsers.project_id)
                               .where(ProjectUsers.user_id == current_user.id)))))