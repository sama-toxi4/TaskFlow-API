from fastapi import APIRouter, Query
from app.schemas.hello import HelloResponse

router = APIRouter()

@router.get("/hello", response_model=HelloResponse)
async def hello_world(name: str = Query("World", min_length=1, max_length=50)) -> dict:
    return {"message": f"Hello, {name}"}