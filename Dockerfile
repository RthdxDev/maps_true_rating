FROM python:3.11-slim

# Установка системных зависимостей для psycopg
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем файлы зависимостей и устанавливаем их
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код приложения
COPY . .

# По умолчанию точка входа — запуск вашего скрипта
CMD ["python", "db/create_db.py"]