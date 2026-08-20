# TaskFlow-API
TaskFlow API — сервис для управления проектами и задачами внутри них.

Основные сущности:  
User — пользователь (email, пароль, имя, роль: admin/user)  
Project — проект (название, описание, владелец)  
Task — задача (название, описание, статус, приоритет, срок, проект, исполнитель)  
Tag — тег (метка для задач)  
Связь многие-ко-многим: Task ↔ Tag, User ↔ Project (участники)  

Функциональность API:  
Регистрация и аутентификация (JWT)  
CRUD для всех сущностей с проверкой прав (владелец, участник, админ)  
Пагинация, фильтрация и сортировка (по статусу, приоритету, проекту, тегам)  
Ролевая модель (админ может управлять пользователями)  
Кэширование частых GET-запросов (Redis)  
Фоновая задача: отправка уведомлений о приближении дедлайна (Celery + Redis)  
Тесты (pytest)  
Docker, docker-compose для локального запуска  
Alembic для миграций БД  
Технологии: Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, Redis, Celery, Pydantic v2, Alembic, Docker, pytest, GitHub Actions (CI).  

# Инструкция по запуску
Для создания виртаульного окружения и установки зависимостей  
Пишем в консоль данные команды в консоль:  

python -m venv venv  
source venv/bin/activate  # для Windows: venv\Scripts\activate  
pip install -r requirements.txt

В случае работы с локальной БД:  
Создайте БД taskflow

Инициируем alembic:  
alembic revision --autogenerate -m "init"  
alembic upgrade head

Запускаем приложение:  
uvicorn app.main:app --reload