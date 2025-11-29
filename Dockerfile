# Используем официальный базовый образ Python 3.11
FROM python:3.11-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы (включая папку api)
COPY . .

# Команда, которая запускается при старте контейнера
# Мы используем Gunicorn для запуска нашего Flask-приложения (Webhook)
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 api.webhook:handler