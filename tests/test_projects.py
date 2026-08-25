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
async def test_create_project(client: AsyncClient):
    token = await register_and_login(client)
    response = await client.post("/api/v1/projects/create_project", json={
        "name": "Test Project",
        "description": "Project description"
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    # Получаем текущего пользователя
    me_resp = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    me_data = me_resp.json()
    assert data["owner_id"] == me_data["id"]

@pytest.mark.asyncio
async def test_create_project_without_token(client: AsyncClient):
    response = await client.post("/api/v1/projects/create_project", json={
        "name": "Test Project",
        "description": "Project description"
    })
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_project_by_id(client: AsyncClient):
    token = await register_and_login(client)
    # Создаём проект
    create_resp = await client.post("/api/v1/projects/create_project", json={
        "name": "Test Project",
        "description": "Project description"
    }, headers={"Authorization": f"Bearer {token}"})
    project_id = create_resp.json()["id"]

    # Получаем проект
    response = await client.get(f"/api/v1/projects/{project_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["id"] == project_id

@pytest.mark.asyncio
async def test_get_project_forbidden(client: AsyncClient):
    token_owner = await register_and_login(client, email="owner@example.com")
    # Создаём проект владельцем
    create_resp = await client.post("/api/v1/projects/create_project", json={
        "name": "Owner Project",
        "description": "desc"
    }, headers={"Authorization": f"Bearer {token_owner}"})
    project_id = create_resp.json()["id"]

    # Регистрируем другого пользователя
    token_other = await register_and_login(client, email="other@example.com")
    # Пытаемся получить чужой проект
    response = await client.get(f"/api/v1/projects/{project_id}", headers={"Authorization": f"Bearer {token_other}"})
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_update_project_owner_success(client: AsyncClient):
    token = await register_and_login(client)
    create_resp = await client.post("/api/v1/projects/create_project", json={
        "name": "Test Project",
        "description": "desc"
    }, headers={"Authorization": f"Bearer {token}"})
    project_id = create_resp.json()["id"]

    response = await client.patch(f"/api/v1/projects/{project_id}", json={
        "name": "Updated Project"
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Project"

@pytest.mark.asyncio
async def test_delete_project_owner_success(client: AsyncClient):
    token = await register_and_login(client)
    create_resp = await client.post("/api/v1/projects/create_project", json={
        "name": "Test Project",
        "description": "desc"
    }, headers={"Authorization": f"Bearer {token}"})
    project_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/projects/{project_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204

    # Проверяем, что проект удалён
    get_resp = await client.get(f"/api/v1/projects/{project_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_resp.status_code == 404