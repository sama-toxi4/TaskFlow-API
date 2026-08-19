from fastapi import APIRouter, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.db.session import get_session
from app.schemas.auth import TokenResponse
from app.schemas.user import UserResponse, UserCreate

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_session)):

    # Проверка на уникальность email
    result = await db.execute(select(User).where(User.email == user_data.email))

    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Создание пользователя
    new_user = User(
        email = user_data.email,
        full_name = user_data.full_name,
        hashed_password = hash_password(user_data.password)
    )

    db.add(new_user)
    await db.commit()
    await db.refresh()
    return new_user


@router.post("login", response_model=TokenResponse)
async def login(
                form_data: OAuth2PasswordRequestForm = Depends(),
                db: AsyncSession = Depends(get_session)):

    # Ищем пользователя по email (в OAuth2PasswordRequestForm поле называется username)
    result = await db.execute(select(User).where(User.email == form_data.username))

    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    # Создаём токен
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}