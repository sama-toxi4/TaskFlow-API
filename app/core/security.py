from datetime import timedelta, timezone, datetime
from typing import Any

import bcrypt
from jose import jwt

from app.core.config import settings


def hash_password(password:str) -> str:
    # 1. Переводим строку пароля в байты
    password_bytes = password.encode('utf-8')

    # 2. Генерируем соль
    salt = bcrypt.gensalt()

    # 3. Хэшируем и декодируем обратно в строку для БД
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Переводим обе строки в байты и сравниваем их через специальный метод
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)