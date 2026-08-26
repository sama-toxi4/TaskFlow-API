from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_current_user, get_task_or_404
from app.db.session import get_session
from app.models.project import Project
from app.models.tag import Tag
from app.models.task import Task, TaskTags
from app.models.user import User, ProjectUsers
from app.schemas.project import PageResponse
from app.schemas.task import TaskResponse, TaskCreate, TaskUpdate
from sqlalchemy import select, or_, func, delete

router = APIRouter()

#CREATE
@router.post("/projects/{project_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
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

        result = await db.execute(select(ProjectUsers).where(ProjectUsers.user_id == current_user.id,
                                                             ProjectUsers.project_id == project_id))
        if not result.scalar_one_or_none():
            raise HTTPException(403, "Not enough permissions")

    # Если назначен исполнитель, проверяем что он участник проекта
    if task_data.assignee_id is not None:
        # Проверяем, что назначаемый пользователь имеет доступ к проекту
        if task_data.assignee_id != project.owner_id:

            member = await db.execute(select(ProjectUsers).where(ProjectUsers.user_id == task_data.assignee_id,
                                                                 ProjectUsers.project_id == project.id))
            if not member.scalar_one_or_none():
                raise HTTPException(403, "Assignee must be a project member")

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
@router.get("/tasks", response_model=PageResponse[TaskResponse])
async def list_tasks(page: int = Query(1, ge=1),
                     per_page: int = Query(10, ge=1, le=100),
                     status: str | None = None,
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
                               .where(ProjectUsers.user_id == current_user.id))))).subquery()

        conditions.append(Task.project_id.in_(select(accessible_projects)))

    if status:
        conditions.append(Task.status == status)
    if priority:
        conditions.append(Task.priority == priority)
    if project_id:
        conditions.append(Task.project_id == project_id)
    if assignee_id:
        conditions.append(Task.assignee_id == assignee_id)
    if due_before:
        conditions.append(Task.due_date <= due_before)
    if due_after:
        conditions.append(Task.due_date >= due_after)
    if conditions:
        query = query.where(*conditions)

    # Пагинация
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    result = await db.execute(query.offset((page-1) * per_page).limit(per_page))
    tasks = result.scalars().all()

    return {"items": tasks,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page if total else 0
            }

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task: Task = Depends(get_task_or_404),
                   db: AsyncSession = Depends(get_session),
                   current_user: User = Depends(get_current_user)) -> TaskResponse:
    project = await db.get(Project, task.project_id)
    if not project:
        raise HTTPException(404, "Project not found")

        # Проверка доступа
    if project.owner_id != current_user.id and current_user.role != "admin":
        # Проверяем участие
        result = await db.execute(select(ProjectUsers).where(ProjectUsers.user_id == current_user.id,
                                                             ProjectUsers.project_id == project.id))

        if not result.scalar_one_or_none():
            raise HTTPException(403, "Not enough permission")

    return task

# UPDATE
@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_update: TaskUpdate,
                      task: Task = Depends(get_task_or_404),
                      db: AsyncSession = Depends(get_session),
                      current_user: User = Depends(get_current_user)) -> TaskResponse:

    project = await db.get(Project, task.project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    # Проверка доступа
    if project.owner_id != current_user.id and current_user.role != "admin":
        # Проверяем участие
        result = await db.execute(select(ProjectUsers).where(ProjectUsers.user_id == current_user.id,
                                                             ProjectUsers.project_id == project.id))

        if not result.scalar_one_or_none():
            raise HTTPException(403, "Not enough permission")

    update_data = task_update.model_dump(exclude_unset = True)

    if project.owner_id == current_user.id or current_user.role == "admin":
        if "tag_ids" in update_data and update_data["tag_ids"] is not None:
            # Удаляем старые связи
            await db.execute(delete(TaskTags).where(TaskTags.task_id == task.id))

            # Добавляем новые
            for tag_id in update_data["tag_ids"]:
                tag = await db.get(Tag, tag_id)
                if not tag:
                    raise HTTPException(404, f"Tag {tag_id} not found")

                db.add(TaskTags(task_id = task.id, tag_id = tag_id))

        if "assignee_id" in update_data and update_data["assignee_id"] is not None:
            new_assignee_id = update_data["assignee_id"]
            if new_assignee_id != project.owner_id:
                member = await db.execute(
                    select(ProjectUsers).where(
                        ProjectUsers.user_id == new_assignee_id,
                        ProjectUsers.project_id == project.id
                    )
                )
                if not member.scalar_one_or_none():
                    raise HTTPException(403, "Assignee must be a project member")

        update_data.pop("tag_ids", None)

        # Владелец/админ могут обновлять все поля
        allowed_fields = set(update_data.keys())
    elif task.assignee_id == current_user.id:
        # Исполнитель может менять только статус
        allowed_fields = {"status"}

        forbidden = set(update_data.keys()) - allowed_fields
        if forbidden:
            raise HTTPException(403, "You can only change status")
    else:
        # Участник, но не владелец и не исполнитель
        raise HTTPException(403, "You cannot update this task")

    for field, value in update_data.items():
        if field in allowed_fields:
            setattr(task, field, value)

    await db.commit()
    await db.refresh(task)
    return task

# DELETE
@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task: Task = Depends(get_task_or_404),
                      db: AsyncSession = Depends(get_session),
                      current_user: User = Depends(get_current_user)):

    project = await db.get(Project, task.project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    # Проверяем права: только владелец проекта или админ
    if project.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(403, "Not enough permission")

    await db.execute(delete(TaskTags).where(TaskTags.task_id == task.id))
    await db.delete(task)
    await db.commit()
    return None