# Использую официальный легковесный образ Python 3.13
FROM python:3.13-slim

# Запрещаю Python записывать файлы кэша .pyc на диск контейнера
ENV PYTHONDONTWRITEBYTECODE=1
# Запрещаю буферизовать вывод (чтобы логи в Docker Desktop были видны мгновенно)
ENV PYTHONUNBUFFERED=1

# Устанавливаю рабочую директорию внутри контейнера
WORKDIR /app

# Устанавливаю системные библиотеки, необходимые для сборки некоторых пакетов Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копирую список зависимостей и устанавливаем их
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копирую весь остальной код моего интернет-магазина Pharma в контейнер
COPY . /app/


# 1. Принудительно выдаю файлу скрипта права на выполнение внутри Linux-системы контейнера.
# Без этого Linux заблокирует запуск управляющего скрипта с ошибкой "Permission denied".
RUN chmod +x /app/entrypoint.sh

# 2. Назначаем мой скрипт главным шлюзом старта. 
# Теперь ЛЮБАЯ команда запуска из docker-compose.yml (command:) будет автоматически проходить через него!
ENTRYPOINT ["/app/entrypoint.sh"]