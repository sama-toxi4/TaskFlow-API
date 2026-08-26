import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, ProjectUsers
from app.models.project import Project
from app.models.task import Task, TaskTags
from app.models.tag import Tag

# Вспомогательная функция регистрации и входа
async def register_and_login(client: AsyncClient, email: str = "user@example.com", password: str = "password123") -> str:
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": "Test User",
        "password": password
    })
    resp = await client.post("/api/v1/auth/login", data={"username": email, "password": password})
    return resp.json()["access_token"]

# Вспомогательная функция создания проекта
async def create_project(client: AsyncClient, token: str, name: str = "Test Project", description: str = "Project desc") -> dict:
    resp = await client.post("/api/v1/projects/create_project", json={
        "name": name,
        "description": description
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    return resp.json()

# Вспомогательная функция добавления пользователя в участники проекта через прямую БД
async def add_project_member(db_session: AsyncSession, project_id: int, user_id: int):
    db_session.add(ProjectUsers(project_id=project_id, user_id=user_id))
    await db_session.commit()

# Вспомогательная функция создания тега через API
async def create_tag(client: AsyncClient, token: str, name: str = "bug") -> dict:
    resp = await client.post("/api/v1/tags/", json={"name": name}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201
    return resp.json()

@pytest.mark.asyncio
async def test_create_task_success_by_owner(client: AsyncClient):
    token = await register_and_login(client)
    project = await create_project(client, token)
    tag = await create_tag(client, token)

    response = await client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={
            "title": "Task 1",
            "description": "Desc",
            "status": "todo",
            "priority": "high",
            "tag_ids": [tag["id"]]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Task 1"
    assert data["project_id"] == project["id"]
    assert data["assignee_id"] is None
    assert data["priority"] == "high"

@pytest.mark.asyncio
async def test_create_task_by_participant_success(client: AsyncClient, db_session):
    # Владелец проекта
    owner_token = await register_and_login(client, email="owner@example.com")
    project = await create_project(client, owner_token)

    # Второй пользователь
    member_token = await register_and_login(client, email="member@example.com")
    # Получаем id участника
    me_resp = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {member_token}"})
    member_id = me_resp.json()["id"]

    # Добавляем участника в проект через БД
    await add_project_member(db_session, project["id"], member_id)

    # Пытаемся создать задачу как участник
    response = await client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"title": "Task by member", "description": "Desc"},
        headers={"Authorization": f"Bearer {member_token}"}
    )
    assert response.status_code == 201

@pytest.mark.asyncio
async def test_create_task_by_non_member_forbidden(client: AsyncClient):
    # Владелец проекта
    owner_token = await register_and_login(client, email="owner@example.com")
    project = await create_project(client, owner_token)

    # Посторонний пользователь
    stranger_token = await register_and_login(client, email="stranger@example.com")

    response = await client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"title": "Forbidden task", "description": "Desc"},
        headers={"Authorization": f"Bearer {stranger_token}"}
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_create_task_with_assignee_not_member_forbidden(client: AsyncClient, db_session):
    # Владелец проекта
    owner_token = await register_and_login(client, email="owner@example.com")
    project = await create_project(client, owner_token)

    # Сторонний пользователь
    outsider_token = await register_and_login(client, email="outsider@example.com")
    me_resp = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {outsider_token}"})
    outsider_id = me_resp.json()["id"]

    # Пытаемся назначить его исполнителем
    response = await client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={
            "title": "Task",
            "description": "Desc",
            "assignee_id": outsider_id
        },
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_list_tasks_with_filters(client: AsyncClient, db_session):
    # Владелец проекта
    token = await register_and_login(client)
    project = await create_project(client, token)

    # Создаём несколько задач с разными статусами и приоритетами
    await client.post(f"/api/v1/projects/{project['id']}/tasks", json={
        "title": "Task 1", "description": "Desc", "status": "todo", "priority": "low"
    }, headers={"Authorization": f"Bearer {token}"})
    await client.post(f"/api/v1/projects/{project['id']}/tasks", json={
        "title": "Task 2", "description": "Desc", "status": "in_progress", "priority": "high"
    }, headers={"Authorization": f"Bearer {token}"})
    await client.post(f"/api/v1/projects/{project['id']}/tasks", json={
        "title": "Task 3", "description": "Desc", "status": "todo", "priority": "medium"
    }, headers={"Authorization": f"Bearer {token}"})

    # Фильтр по статусу todo
    resp = await client.get("/api/v1/tasks?status=todo", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2

    # Фильтр по приоритету high
    resp = await client.get("/api/v1/tasks?priority=high", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Task 2"

    # Фильтр по project_id
    resp = await client.get(f"/api/v1/tasks?project_id={project['id']}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3

@pytest.mark.asyncio
async def test_get_task_by_owner(client: AsyncClient):
    token = await register_and_login(client)
    project = await create_project(client, token)
    # Создаём задачу
    create_resp = await client.post(f"/api/v1/projects/{project['id']}/tasks", json={
        "title": "Task", "description": "Desc"
    }, headers={"Authorization": f"Bearer {token}"})
    task_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/tasks/{task_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == task_id
    assert data["title"] == "Task"

@pytest.mark.asyncio
async def test_get_task_by_non_member_forbidden(client: AsyncClient):
    # Владелец
    owner_token = await register_and_login(client, email="owner@example.com")
    project = await create_project(client, owner_token)
    create_resp = await client.post(f"/api/v1/projects/{project['id']}/tasks", json={
        "title": "Task", "description": "Desc"
    }, headers={"Authorization": f"Bearer {owner_token}"})
    task_id = create_resp.json()["id"]

    # Посторонний
    stranger_token = await register_and_login(client, email="stranger@example.com")
    resp = await client.get(f"/api/v1/tasks/{task_id}", headers={"Authorization": f"Bearer {stranger_token}"})
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_update_task_by_owner(client: AsyncClient):
    token = await register_and_login(client)
    project = await create_project(client, token)
    create_resp = await client.post(f"/api/v1/projects/{project['id']}/tasks", json={
        "title": "Original", "description": "Desc"
    }, headers={"Authorization": f"Bearer {token}"})
    task_id = create_resp.json()["id"]

    resp = await client.patch(f"/api/v1/tasks/{task_id}", json={
        "title": "Updated",
        "status": "done"
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Updated"
    assert data["status"] == "done"

@pytest.mark.asyncio
async def test_update_task_by_assignee_only_status(client: AsyncClient, db_session):
    # Владелец
    owner_token = await register_and_login(client, email="owner@example.com")
    project = await create_project(client, owner_token)

    # Участник, он же исполнитель
    assignee_token = await register_and_login(client, email="assignee@example.com")
    me_resp = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {assignee_token}"})
    assignee_id = me_resp.json()["id"]

    # Добавляем участника в проект
    await add_project_member(db_session, project["id"], assignee_id)

    # Создаём задачу с назначением исполнителя
    create_resp = await client.post(f"/api/v1/projects/{project['id']}/tasks", json={
        "title": "Task", "description": "Desc", "assignee_id": assignee_id
    }, headers={"Authorization": f"Bearer {owner_token}"})
    task_id = create_resp.json()["id"]

    # Пытаемся обновить только статус
    resp = await client.patch(f"/api/v1/tasks/{task_id}", json={"status": "done"}, headers={"Authorization": f"Bearer {assignee_token}"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"

    # Пытаемся обновить другое поле (например, title) — должно быть 403
    resp = await client.patch(f"/api/v1/tasks/{task_id}", json={"title": "New title"}, headers={"Authorization": f"Bearer {assignee_token}"})
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_update_task_by_participant_not_assignee_forbidden(client: AsyncClient, db_session):
    # Владелец
    owner_token = await register_and_login(client, email="owner@example.com")
    project = await create_project(client, owner_token)

    # Участник, не исполнитель
    member_token = await register_and_login(client, email="member@example.com")
    me_resp = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {member_token}"})
    member_id = me_resp.json()["id"]
    await add_project_member(db_session, project["id"], member_id)

    # Создаём задачу без исполнителя
    create_resp = await client.post(f"/api/v1/projects/{project['id']}/tasks", json={
        "title": "Task", "description": "Desc"
    }, headers={"Authorization": f"Bearer {owner_token}"})
    task_id = create_resp.json()["id"]

    # Пытаемся обновить
    resp = await client.patch(f"/api/v1/tasks/{task_id}", json={"status": "done"}, headers={"Authorization": f"Bearer {member_token}"})
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_delete_task_by_owner(client: AsyncClient):
    token = await register_and_login(client)
    project = await create_project(client, token)
    create_resp = await client.post(f"/api/v1/projects/{project['id']}/tasks", json={
        "title": "Task", "description": "Desc"
    }, headers={"Authorization": f"Bearer {token}"})
    task_id = create_resp.json()["id"]

    resp = await client.delete(f"/api/v1/tasks/{task_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 204

    # Проверяем, что задача удалена
    resp = await client.get(f"/api/v1/tasks/{task_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_delete_task_by_non_owner_forbidden(client: AsyncClient, db_session):
    # Владелец
    owner_token = await register_and_login(client, email="owner@example.com")
    project = await create_project(client, owner_token)
    create_resp = await client.post(f"/api/v1/projects/{project['id']}/tasks", json={
        "title": "Task", "description": "Desc"
    }, headers={"Authorization": f"Bearer {owner_token}"})
    task_id = create_resp.json()["id"]

    # Участник, но не владелец
    member_token = await register_and_login(client, email="member@example.com")
    me_resp = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {member_token}"})
    member_id = me_resp.json()["id"]
    await add_project_member(db_session, project["id"], member_id)

    resp = await client.delete(f"/api/v1/tasks/{task_id}", headers={"Authorization": f"Bearer {member_token}"})
    assert resp.status_code == 403