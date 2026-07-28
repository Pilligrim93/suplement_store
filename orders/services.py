




import redis        # redis-py БИБИЛИОТЕКА не путать с бд
from django.conf import settings
from redis.exceptions import LockError

# Создаем готовые соединения (socket_client_django tcp socket_server_redis)
# REDIS_POOL = до 50 вечно работающих соединений - обслуживание запросов клиентов.
REDIS_POOL = redis.ConnectionPool(
    host=getattr(settings, 'REDIS_HOST', 'redis'),      
    port=getattr(settings, 'REDIS_PORT', 6379),
    db=0,                           # номер бд 0/15
    decode_responses=True,          # Декодирует байты в строку на выходе зи Redis
    max_connections=50,             # Потолок открытых сокетов
    socket_connect_timeout=2,       # Таймаут на установку связи
    socket_timeout=5,               # Таймаут на выполнение команды
    retry_on_timeout=True,          # Авто-повтор при микро-лагах сети
    health_check_interval=30        # Пинг туннелей каждые 30 секунд для очистки мертвых сокетов
)


class OrderService:
    """
    Архитектурное ядро обработки заказов Pharma (Highload-версия 2026).
    Управляет транзакциями в Redis, безопасными блокировками и Celery.
    """

    _LUA_RESERVE_STOCK = """
        -- 1. Одним атомарным запросом читаем остатки СРАЗУ ВСЕХ товаров из корзины
        local all_stocks = redis.call('mget', unpack(KEYS))
        
        -- 2. ЭТАП ПРОВЕРКИ (работаем со считанным массивом в памяти Lua)
        for i = 1, #KEYS do
            local current_stock = all_stocks[i]

            -- Конвертация в int естли есть товар или 0 если нет 
            local actual_count = current_stock and tonumber(current_stock) or 0

            -- Если товара нет в кэше или его количество меньше, чем просит юзер
            if actual_count < tonumber(ARGV[i]) then
                return 0  -- Мгновенный отказ, ничего не списываем!
            end
        end

        -- 3. ЭТАП РЕЗЕРВА (если всё в порядке — списываем остатки)
        for i = 1, #KEYS do 
            redis.call('decrby', KEYS[i], ARGV[i])
        end

        return 1  -- Успешное резервирование!
    """

    
    def __init__(self, request, idempotency_key: str, cart_items):
        self.request = request
        self.idempotency_key = idempotency_key
        self.cart_items = cart_items

        # Пульт управления redis-py и передали настройки pool(socket) 
        self.redis_client = redis.Redis(connection_pool=REDIS_POOL)

        # Создаем исполняемый Python-объект для нашего Lua-скрипта
        self.lua_script = self.redis_client.register_script(self._LUA_RESERVE_STOCK)


    def process_checkout(self, cleaned_data: dict):
        """
        Главный бизнес-конвейер оформления заказа.
        Возвращает: (Статус_Успеха, Текст_Ошибки)
        """
        redis_idem_key = f"idem:{self.idempotency_key}"
        
        # --- ШАГ 3 Защита от дубликатов запросов по UUID ---
        # Атомарно проверяет и если нет UUID в
        # блоке блокирует на 5 мин иначе возвращает False 
        is_unique = self.redis_client.set(redis_idem_key, "IN_PROGRESS", nx=True, ex=300)
        if is_unique is False:
            return False, "Ваш заказ уже обрабатывается или этот запрос является дубликатом."
        
        # lock:user/anon дописываем для сортировки блокировки по user/anon
        if self.request.user.is_authenticated:
            lock_key = f"lock:user:{self.request.user.id}"
        else:
            lock_key = f"lock:anon:{self.request.session.session_key}"
        
        # Создаем замок через встроенный инструмент redis-py.
        # timeout=5 время жизни замка через 5 сек при падении сервера.
        # blocking=False говорит: если замок занят, сразу возвращать False, а не ждать в цикле.
        client_lock = self.redis_client.lock(lock_key, timeout=5, blocking=False)

        try:
            with client_lock:
                # --- ШАГ 5: ИСПОЛНЕНИЕ LUA-СКРИПТА ОСТАТКОВ ИЗ БИБЛИОТЕКИ ---
                # Синхронно готовим списки ключей и их количеств для передачи в Redis
                keys = [f"product:stock:{item.product.id}" for item in self.cart_items]
                argv = [item.quantity for item in self.cart_items]
                
                # Вызываем Lua-скрипт ожидается 1/0 прошла проверка или нет
                result = self.lua_script(keys=keys, args=argv)

                if result == 0:
                    # Если сработал отказ в Lua — удаляем order, чтобы юзер мог пересобрать корзину
                    self.redis_client.delete(redis_idem_key)
                    return False, "Одного или нескольких товаров из вашей корзины больше нет на складе!"


            # --- ШАГ 6: ТУТ БУДЕТ ВЫЗОВ В ФОН CELERY ДЛЯ ПОСТ-ЗАПИСИ В POSTGRESQL ---
            # task_create_order.delay(...)
            

            # Переводим талончик в статус SUCCESS на сутки
            # Защита от дублирующих заказов
            self.redis_client.set(redis_idem_key, "SUCCESS", ex=86400)
            return True, None
        
        except redis.exceptions.LockError:
            # Срабатывает мгновенно, если клиент кликнул из параллельной вкладки браузера
            return False, "Вы уже оформляете заказ в другой вкладке. Пожалуйста, подождите."


        except Exception as e:
            # При любом непредвиденном сбое бэкенда — 
            # зачищаем талончик идемпотентности для рестарта
            self.redis_client.delete(redis_idem_key)
            return False, f"Критическая ошибка при обработке заказа: {str(e)}"

        



            


# import redis
# from django.conf import settings

# #  ГЛАВНЫЙ СИНГЛТОН-ПУЛ (На уровне модуля)
# # Создаётся ровно ОДИН раз при запуске Docker-контейнера Django.
# # Предотвращает оверхед на пересоздание TCP-соединенней при каждом запросе.
# REDIS_POOL = redis.ConnectionPool(
#     host=getattr(settings, 'REDIS_HOST', 'redis'),
#     port=getattr(settings, 'REDIS_PORT', 6379),
#     db=0,
#     decode_responses=True,
#     max_connections=50  # Потолок соединений, защищающий Redis от перегрузки
# )


# class OrderService:
#     """
#     Архитектурное ядро обработки заказов Pharma (Highload-версия 2026).
#     Управляет транзакциями в Redis, безопасными блокировками и Celery.
#     """
    
#     #  Оптимизированный Lua-скрипт на базе MGET. Возвращает только 0 или 1.
#     _LUA_RESERVE_STOCK = """
#         -- 1. Одним атомарным запросом читаем остатки СРАЗУ ВСЕХ товаров из корзины
#         local all_stocks = redis.call('mget', unpack(KEYS))
        
#         -- 2. ЭТАП ПРОВЕРКИ (работаем со считанным массивом в памяти Lua)
#         for i = 1, #KEYS do
#             local current_stock = all_stocks[i]

#             -- Если товара нет в кэше вообще, считаем его остаток за 0
#             local actual_count = current_stock and tonumber(current_stock) or 0

#             -- Если товара нет в кэше или его количество меньше, чем просит юзер
#             if not current_stock or actual_count < tonumber(ARGV[i]) then
#                 return 0  -- Мгновенный отказ, ничего не списываем!
#             end
#         end

#         -- 3. ЭТАП РЕЗЕРВА (если всё в порядке — списываем остатки)
#         for i = 1, #KEYS do 
#             redis.call('decrby', KEYS[i], ARGV[i])
#         end

#         return 1  -- Успешное резервирование!
#     """

#     def __init__(self, request, idempotency_key: str, cart_items):
#         self.request = request
#         self.idempotency_key = idempotency_key
#         self.cart_items = cart_items

#         #  Мгновенно берём готовое соединение из глобального вечного пула
#         self.redis_client = redis.Redis(connection_pool=REDIS_POOL)

#         # Кэшируем Lua-скрипт в памяти Redis один раз через быструю SHA-1 компиляцию
#         self.lua_script = self.redis_client.register_script(self._LUA_RESERVE_STOCK)

#     def process_checkout(self, cleaned_data: dict) -> tuple[bool, str | None]:
#         """
#         Главный бизнес-конвейер оформления заказа.
#         Возвращает: (Статус_Успеха, Текст_Ошибки)
#         """
#         redis_idem_key = f"idem:{self.idempotency_key}"
        
#         # --- ШАГ 3: Защита от дубликатов запросов по UUID (SET NX) ---
#         is_unique = self.redis_client.set(redis_idem_key, "IN_PROGRESS", nx=True, ex=300)
#         if is_unique is False:
#             return False, "Ваш заказ уже обрабатывается или этот запрос является дубликатом."
        
#         # --- ШАГ 4: Настройка распределенного замка по User/Session ---
#         if self.request.user.is_authenticated:
#             lock_key = f"lock:user:{self.request.user.id}"
#         else:
#             lock_key = f"lock:anon:{self.request.session.session_key}"
        
#         # Конфигурируем замок (неблокирующий Highload-режим)
#         client_lock = self.redis_client.lock(lock_key, timeout=5, blocking=False)

#         # Вставляем наш client_lock в автоматическую кнопку-контекст Python
#         try:
#             with client_lock:
#                 # --- ШАГ 5: ИСПОЛНЕНИЕ LUA-СКРИПТА ОСТАТКОВ ---
#                 keys = [f"product:stock:{item.product.id}" for item in self.cart_items]
#                 argv = [item.quantity for item in self.cart_items]  # Зеркало Lua ARGV

#                 # Запуск кэшированного Lua-скрипта через быструю команду EVALSHA под капотом
#                 result = self.lua_script(keys=keys, args=argv)

#                 if result == 0:
#                     # Если сработал отказ в Lua — удаляем талончик, чтобы юзер мог повторить попытку после редиректа
#                     self.redis_client.delete(redis_idem_key)
#                     return False, "Одного или нескольких товаров из вашей корзины больше нет на складе в нужном количестве."
                
#                 # --- ШАГ 6: ТУТ БУДЕТ ВЫЗОВ В ФОН CELERY ДЛЯ ПОСТ-ЗАПИСИ В POSTGRESQL ---
#                 # task_create_order.delay(...)

#                 # Заказ успешно обработан, фиксируем талончик идемпотентности на сутки
#                 self.redis_client.set(redis_idem_key, "SUCCESS", ex=86400)
#                 return True, None

#         except redis.exceptions.LockError:
#             # Срабатывает мгновенно, если клиент кликнул из параллельной вкладки браузера
#             return False, "Вы уже оформляете заказ в другой вкладке. Пожалуйста, подождите."

#         except Exception as e:
#             # Защита от любых внештатных падений инфраструктуры — открываем талончик для рестарта
#             self.redis_client.delete(redis_idem_key)
#             return False, f"Критическая ошибка при обработке заказа: {str(e)}"





















