import pytest
from httpx import AsyncClient

async def register_and_login(client: AsyncClient, email="user@example.com", password="password123"):
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": "Test User",
        "password": password
    })
    resp = await client.post("/api/v1/auth/login", data={"username": email, "password": password})
    return resp.json()["access_token"]

@pytest.mark.asyncio
async def test_create_tag_success(client: AsyncClient):
    token = await register_and_login(client)
    response = await client.post("/api/v1/tags/", json={"name": "bug"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "bug"
    assert "id" in data

@pytest.mark.asyncio
async def test_create_tag_duplicate(client: AsyncClient):
    token = await register_and_login(client)
    await client.post("/api/v1/tags/", json={"name": "bug"}, headers={"Authorization": f"Bearer {token}"})
    response = await client.post("/api/v1/tags/", json={"name": "bug"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_list_tags(client: AsyncClient):
    token = await register_and_login(client)
    # Создаём два тега
    await client.post("/api/v1/tags/", json={"name": "bug"}, headers={"Authorization": f"Bearer {token}"})
    await client.post("/api/v1/tags/", json={"name": "feature"}, headers={"Authorization": f"Bearer {token}"})
    response = await client.get("/api/v1/tags/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    tags = response.json()
    assert len(tags) == 2
    # Проверяем, что имена совпадают (порядок может быть по алфавиту)
    names = {tag["name"] for tag in tags}
    assert names == {"bug", "feature"}

@pytest.mark.asyncio
async def test_delete_tag_forbidden_for_non_admin(client: AsyncClient):
    token = await register_and_login(client)
    # Создаём тег
    create_resp = await client.post("/api/v1/tags/", json={"name": "bug"}, headers={"Authorization": f"Bearer {token}"})
    tag_id = create_resp.json()["id"]
    # Пытаемся удалить (роль user)
    response = await client.delete(f"/api/v1/tags/{tag_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_delete_tag_by_admin_success(client: AsyncClient, db_session):
    # Регистрируем пользователя
    token = await register_and_login(client, email="admin@example.com")
    # Получаем id пользователя
    me_resp = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    user_id = me_resp.json()["id"]

    # Обновляем роль на admin в тестовой БД
    from app.models.user import User
    user = await db_session.get(User, user_id)
    user.role = "admin"
    await db_session.commit()

    # Создаём тег
    create_resp = await client.post("/api/v1/tags/", json={"name": "bug"}, headers={"Authorization": f"Bearer {token}"})
    tag_id = create_resp.json()["id"]

    # Удаляем тег админом
    response = await client.delete(f"/api/v1/tags/{tag_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204