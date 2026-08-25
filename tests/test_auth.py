import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={
        "email": "user@example.com",
        "full_name": "Test User",
        "password": "password123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "user@example.com"
    assert "id" in data

@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    # Сначала регистрируем
    await client.post("/api/v1/auth/register", json={
        "email": "user@example.com",
        "full_name": "Test User",
        "password": "password123"
    })
    # Повторная регистрация с тем же email
    response = await client.post("/api/v1/auth/register", json={
        "email": "user@example.com",
        "full_name": "Another User",
        "password": "password456"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    # Регистрируем пользователя
    await client.post("/api/v1/auth/register", json={
        "email": "user@example.com",
        "full_name": "Test User",
        "password": "password123"
    })
    # Логинимся
    response = await client.post("/api/v1/auth/login", data={
        "username": "user@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    # Регистрируем
    await client.post("/api/v1/auth/register", json={
        "email": "user@example.com",
        "full_name": "Test User",
        "password": "password123"
    })
    # Пытаемся войти с неверным паролем
    response = await client.post("/api/v1/auth/login", data={
        "username": "user@example.com",
        "password": "wrongpass"
    })
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_me(client: AsyncClient):
    # Регистрируем и логинимся
    await client.post("/api/v1/auth/register", json={
        "email": "user@example.com",
        "full_name": "Test User",
        "password": "password123"
    })
    login_resp = await client.post("/api/v1/auth/login", data={
        "username": "user@example.com",
        "password": "password123"
    })
    token = login_resp.json()["access_token"]

    # Запрос /users/me с токеном
    response = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "user@example.com"
    assert data["full_name"] == "Test User"

    # Запрос без токена
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401