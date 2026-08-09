# Используем официальный легковесный образ Python 3.13
FROM python:3.13-slim

# Запрещаем Python записывать файлы кэша .pyc на диск контейнера
ENV PYTHONDONTWRITEBYTECODE=1
# Запрещаем буферизовать вывод (чтобы логи в Docker Desktop были видны мгновенно)
ENV PYTHONUNBUFFERED=1

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Устанавливаем системные библиотеки, необходимые для сборки некоторых пакетов Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копируем список зависимостей и устанавливаем их
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код моего интернет-магазина Pharma в контейнер
COPY . /app/
