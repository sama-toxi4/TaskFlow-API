from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.db.session import get_session
from app.models.project import Project
from app.models.task import Task
from app.models.user import User, ProjectUsers

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_session)) -> User:

    credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))

    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user

async def get_project_or_404(project_id: int, db:AsyncSession = Depends(get_session)) -> Project:
    project = await db.get(Project, project_id)

    if not project:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Project not found")

    return project

async def check_project_access(project: Project = Depends(get_project_or_404),
                               current_user: User = Depends(get_current_user),
                               db: AsyncSession = Depends(get_session)) -> Project:

    # Проверяем, является ли пользователь владельцем, участником или админом
    if project.owner_id == current_user.id or current_user.role == "admin":
        return project

    result = await db.execute(select(ProjectUsers).where(ProjectUsers.project_id == project.id, ProjectUsers.user_id == current_user.id))

    if not result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return project

async def check_project_owner(project: Project = Depends(get_project_or_404),
                              current_user: User = Depends(get_current_user)) -> Project:

    if project.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return project

async def get_task_or_404(task_id: int,
                          db:AsyncSession = Depends(get_session)) -> Task:
    task = await db.get(Task, task_id)

    if not task:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "Task not found")

    return task

async def check_task_assigned(task: Task = Depends(get_task_or_404),
                              current_user: User = Depends(get_current_user)) -> Task:

    if task.assignee_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return task