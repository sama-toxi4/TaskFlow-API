# Базовый образ с Python
FROM python:3.13-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Открываем порт для FastAPI
EXPOSE 8000

# Команда запуска приложения (можем переопределить в compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]