
import redis
from orders.services import REDIS_POOL


class CartService:
    # Твой эталонный, вычищенный Lua-скрипт слияния корзин со всеми индексами
    _LUA_MERGE_SCRIPT = """
    -- [[ HGETALL - все товары корзины,  KEYS[1] - аноним ]]
    local guest_cart = redis.call('HGETALL', KEYS[1])

    -- [[ Обращаемся к первому product_id если его нет то заканчиваем. ]]
    if not guest_cart[1] then 
        return 0 
    end

    -- [[ Получаем field=id, qty=quantity отдельно. ]]
    for i = 1, #guest_cart, 2 do
        local field = guest_cart[i]
        local qty = tonumber(guest_cart[i+1])

    -- [[ Если количество есть и больше нуля к корзине пользователя ]] 
    -- [[ прибавляем, уменьшаем или добавляем товары из корзины анонима ]]
        if qty and qty > 0 then
            redis.call('HINCRBY', KEYS[2], field, qty)
        end
    end

    redis.call('DEL', KEYS[1])
    -- [[ Задали ttl для user ]]
    redis.call('EXPIRE', KEYS[2], tonumber(ARGV[1]))
    return 1
    """

    def __init__(self, user_id: int = None, guest_token: str = None):
        """
        Универсальный конструктор без связанности с request.
        Работает с ID юзера из Postgres или Guest Token из Cookie/Заголовков.
        """
        self.redis_client = redis.Redis(connection_pool=REDIS_POOL)
        self.ttl = 2592000  # 30 дней жизни корзины

        # Локальный внутризапросный кэш «вспышка»
        self._cached_items = None

        # Формируем именной ключ в Redis без оглядки на сессии Django
        if user_id:
            self.cart_key = f"cart:user:{user_id}"
        elif guest_token:
            self.cart_key = f"cart:anon:{guest_token}"
        else:
            raise ValueError(
                "CartService требует обязательный user_id или guest_token"
            )

        # Регистрируем наш Lua-скрипт в оперативной памяти Redis при старте сервиса 
        self.lua_merge = self.redis_client.register_script(
            self._LUA_MERGE_SCRIPT
        )

    def get_items(self) -> list[dict]:
        """Вытаскивает легкую корзину и обогащает ее БЕЗ избыточных повторных запросов в сокет"""
        # Если этот метод запускали хоть раз в течении 
        # запроса то cache не пуст а сделает свою работу
        if self._cached_items is not None:
            return self._cached_items

        raw_cart = self.redis_client.hgetall(self.cart_key)
        if not raw_cart:
            # ВАЖНО специально задали значение [] если где то еще вызовут 
            # этот метод то он не будет делать не какой запрос по socket а 
            # сразу из cached_items выдаст ответ пусто, нет лишних соединений.
            self._cached_items = []
            return self._cached_items

        product_ids = list(raw_cart.keys())

        # Открываем pipeline для пакетного сбора данных каталога (защита от сетевых лагов)
        pipe = self.redis_client.pipeline()
        for p_id in product_ids:
            # Важно f"catalog:product:{p_id}" - целый ключ не поле.
            pipe.hmget(f"catalog:product:{p_id}", ["name", "price", "image"])

        # Запуск pipeline пакета запросов разом, 
        # вернуться 3 поля ["name", "price", "image"]
        catalog_data_list = pipe.execute()

        enriched_items = []
        for p_id, catalog_fields in zip(product_ids, catalog_data_list):
            qty = int(raw_cart[p_id])   # Обращаеясь к id получаем quantity 

            if catalog_fields and catalog_fields[0] is not None:
                price_val = catalog_fields[1]
                # Проерка цены что существует и что только цифры.
                price = (int(price_val) if price_val and str(price_val).isdigit() else 0)

                # Сборка корзины.
                enriched_items.append(
                    {
                        "product_id": int(p_id),
                        "quantity": qty,
                        "name": catalog_fields[0],
                        "price": price,
                        "total_price_line": qty * price,
                        "image": catalog_fields[2] or "",
                    }
                )
        # Обновляем время жизни корзины при активности
        self.redis_client.expire(self.cart_key, self.ttl)
        self._cached_items = enriched_items
        return self._cached_items

    def add_or_update_item(self, product_id: int, quantity: int) -> bool:
        """Атомарное изменение количества с проверкой существования товара в кэше каталога"""
        catalog_key = f"catalog:product:{product_id}"

        if not self.redis_client.exists(catalog_key):
            return False

        # Вернет остаток в корзине.
        new_qty = self.redis_client.hincrby(self.cart_key, str(product_id), quantity)

        if new_qty <= 0:
            self.redis_client.hdel(self.cart_key, str(product_id))

        # Обновляем время жизни корзины при активности
        self.redis_client.expire(self.cart_key, self.ttl)
        self._cached_items = None
        return True

    def remove_item(self, product_id: int) -> None:
        """Точечное моментальное удаление всей товарной позиции из Хэша"""
        self.redis_client.hdel(self.cart_key, str(product_id))
        
        # Обновляем время жизни корзины при активности
        self.redis_client.expire(self.cart_key, self.ttl)
        self._cached_items = None

    def total_quantity(self) -> int:
        """Счетчик штук товаров в ОП бэкенда БЕЗ повторных сетевых запросов"""
        return sum(item["quantity"] for item in self.get_items())

    def total_price(self) -> int:
        """Счетчик суммы корзины (0 холостых запросов к СУБД и Redis)"""
        return sum(item["total_price_line"] for item in self.get_items())

    def clear(self) -> None:
        """Полное удаление ключа корзины клиента из ОП"""
        self.redis_client.delete(self.cart_key)
        self._cached_items = None

    def merge_guest_cart(self, guest_token: str) -> None:
        """Слияние гостевой корзины с профильной через твой Lua-скрипт (1 укол в сеть)"""
        if not guest_token:
            return

        guest_key = f"cart:anon:{guest_token}"

        # Запускаем мой скрипт. Передаем KEYS[1]=гость, KEYS[2]=юзер, ARGV[1]=ttl
        self.lua_merge(keys=[guest_key, self.cart_key], args=[self.ttl])

        # Полностью сбрасываем локальный внутризапросный кэш Python
        self._cached_items = None






# Запустить и посмотреть как работает магазин а так же решить проблему если она есть с суммой в строке товара







































