from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def read_currend_user(currend_user: User = Depends(get_current_user)):
    return currend_user