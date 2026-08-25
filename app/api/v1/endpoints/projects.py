from fastapi import APIRouter, Query, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.api.dependencies import get_current_user, check_project_access, check_project_owner
from app.db.session import get_session
from app.models.project import Project
from app.models.user import User, ProjectUsers
from app.schemas.project import ProjectResponse, PageResponse, ProjectCreate, ProjectUpdate

router = APIRouter()

# CREATE
@router.post("/create_project", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(project_data: ProjectCreate,
                         db: AsyncSession = Depends(get_session),
                         current_user: User = Depends(get_current_user)) -> ProjectResponse:

    # Проверка на уникальность name
    result = await db.execute(select(Project).where(Project.name == project_data.name))

    if result.scalar_one_or_none():
        raise HTTPException(400, "Project with this name already exists")

    new_project = Project(
        name = project_data.name,
        description = project_data.description,
        owner_id = current_user.id
    )

    db.add(new_project)
    await db.flush()

    db.add(ProjectUsers(project_id = new_project.id, user_id = current_user.id))
    await db.commit()
    await db.refresh(new_project)

    return new_project

# READ
@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project: Project = Depends(check_project_access)) -> ProjectResponse:
    return project

@router.get("/", response_model=PageResponse[ProjectResponse])
async def list_projects(
    page: int = Query(1, ge=1),
    per_page: int = Query(1, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
                        ):

    if current_user.role == "admin":
        base_query = select(Project)
    else:
        base_query = (select(Project).join(ProjectUsers, ProjectUsers.project_id == Project.id, isouter=True)
                    .where(or_(Project.owner_id == current_user.id, ProjectUsers.user_id == current_user.id)).distinct())


    total_query = select(func.count()).select_from(base_query.subquery())
    total = await db.scalar(total_query) or 0

    result = await db.execute(base_query.offset((page - 1) * per_page).limit(per_page))

    projects = result.scalars().all()

    return {
        "items": projects,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page if total > 0 else 0
    }

# UPDATE
@router.patch("/{project_id}",response_model=ProjectResponse)
async def update_project(project_update: ProjectUpdate,
                         project: Project = Depends(check_project_owner),
                         db: AsyncSession = Depends(get_session)) -> ProjectResponse:

    update_data = project_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)

    return project

# DELETE
@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project: Project = Depends(check_project_owner),
                         db: AsyncSession = Depends(get_session)):

    await db.delete(project)
    await db.commit()
    return None


