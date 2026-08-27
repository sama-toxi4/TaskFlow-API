from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.redis import get_cache, set_cache, delete_cache
from app.db.session import get_session
from app.models.tag import Tag
from app.models.user import User
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
    # Удаляем кеш
    await delete_cache("tags:all")

    return new_tag

#READ
# noinspection PyTypeChecker
@router.get("/", response_model=list[TagResponse])
async def list_tags(db:AsyncSession = Depends(get_session)) -> list[TagResponse]:
    cached_tags = await get_cache("tags:all")
    if cached_tags:
        return cached_tags

    result= await db.execute(select(Tag).order_by(Tag.name))
    tags = result.scalars().all()

    await set_cache("tags:all", [TagResponse.model_validate(tag).model_dump() for tag in tags])
    return tags

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
    # Удаляем кеш
    await delete_cache("tags:all")

    return None