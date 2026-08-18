from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends
from sqlalchemy import text
from app.db.session import get_session

router = APIRouter()

@router.get("/db-check")
async def db_check(db:AsyncSession = Depends(get_session)) -> dict:

    query = text("SELECT 1")

    await db.execute(query)

    return {"db": "ok"}