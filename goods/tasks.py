from celery import shared_task

@shared_task(
    bind=True,                      # Добавляем self - celery для получения доступа к новым методам. 
    acks_late=True,                 # Защита от утери задачи при падении или перезапуске воркера
    default_retry_delay=5,          # Бережная пауза в 5 секунд перед авто-повтором
    max_retries=3                   # Всего 3 попытки, если сеть между контейнерами моргнет
)

def task_update_products_cache_batch(self, product_ids: list[int]) -> str:
    """
    Асинхронный конвейер Celery (Инстанс №3, Порт 6381).
    Принимает ПАЧКУ ID товаров за один раз.
    Обновляет свойства товаров в ОП 4-го инстанса по Pipeline.
    """
    if not product_ids:
        return "Действие отменено: передан пустой список идентификаторов"

    try:
        # ЗАЩИТА СТАРТА: Импортирую сервис строго внутри тела функции,
        # чтобы Celery не упал в ошибку AppRegistryNotReady при инициализации Django.
        from goods.services import CatalogCacheService
        
        cache_service = CatalogCacheService()
        
        # Запускаю пачечный метод (1 укол в Postgres и 1 Pipeline в Redis)
        # Кол-во перезаписаных товаров в пачке для кеша.
        count = cache_service.write_products_batch_in_cache(product_ids)
        
        return f" [Highload Batch] Успешно обновлена пачка из {count} товаров в redis_catalog"
        
    except Exception as exc:
        # Если база данных была занята или отовалился сокет — Celery бережно повторит задачу
        raise self.retry(exc=exc)


@shared_task(                       
    bind=True,                      # Добавляем self - celery для получения доступа к новым методам.
    acks_late=True,                 # Защита от утери задачи при падении или перезапуске воркера
    default_retry_delay=10,         # Пауза в 5 секунд перед авто-повтором
    max_retries=3                   # Всего 3 попытки, если сеть между контейнерами моргнет
)
def task_write_all_catalog_in_cache(self) -> str:
    """
    (Инстанс №3, Порт 6381).
    Полный пакетный прогрев (заливка) ВСЕГО каталога товаров с нуля в ОП 4-го инстанса.
    Использую для первой инициализации.
    """
    try:
        from goods.services import CatalogCacheService
        
        cache_service = CatalogCacheService()
        
        # Вызываем атомный метод полной перезаписи ОЗУ 4-го инстанса (redis_catalog:6382)
        # Кол-во перезаписаных товаров для кеша весь каталог.
        count = cache_service.write_all_catalog_in_cache()
        
        return f" [Highload Warmup] Каталог полностью прогрет! Залито: {count} товаров в ОЗУ."
        
    except Exception as exc:
        # Если база данных временно недоступна (например, идет бэкап) — повторить попытку
        raise self.retry(exc=exc)


