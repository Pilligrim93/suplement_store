import os 
from celery import Celery

# Задаем дефолтные настройки Django для утилиты celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Читаем конфигурацию из settings.py. 
# Настройки Celery должны начинаться с префикса CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически ищем задачи (файлы tasks.py) 
# во всех зарегистрированных приложениях (включая orders)
app.autodiscover_tasks()



