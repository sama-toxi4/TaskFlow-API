from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.models.tag import Tag
from sqlalchemy import select
from app.schemas.tag import TagResponse, TagCreate

router = APIRouter()

#CREATE
@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(tag_data: TagCreate,
                     db: AsyncSession = Depends(get_session),
                     current_user: User = Depends(get_current_user)) -> TagResponse:
    # Проверка уникальности имени
    result = await db.execute(select(Tag).where(Tag.name == tag_data.name))

    if result.scalar_one_or_none():
        raise HTTPException(400, "Tag with this name already exists")

    new_tag = Tag(name = tag_data.name)

    db.add(new_tag)
    await db.commit()
    await db.refresh(new_tag)

    return new_tag

#READ
@router.get("/", response_model=list[TagResponse])
async def list_tags(db:AsyncSession = Depends(get_session),
                    current_user: User = Depends(get_current_user)) -> list[TagResponse]:
    result = await db.execute(select(Tag).order_by(Tag.name))
    return result.scalars().all()

#DELETE
@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: int,
                     db: AsyncSession = Depends(get_session),
                     current_user: User = Depends(get_current_user)):
    # Проверяем права
    if current_user.role != "admin":
        raise HTTPException(403, "Not enough permissions")

    tag = await db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(404, "Tag not found")

    await db.delete(tag)
    await db.commit()
    return None