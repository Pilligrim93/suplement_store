
import json
from django.core.cache import cache
from django.db import transaction
from goods.models import Product
from carts.models import Cart, CartItem



class RedisAnonCartItem:
    """Виртуальная модель одной строки товара для анонимов (имитация CartItem), 
    для того чтобы  HTML-шаблоны могли обращаться к обьектам и их свойствам {{ item.product.name }} 
    """
    def __init__(self, product, quantity, price_at_addition):
        self.product = product
        self.quantity = quantity
        self.price_at_addition = price_at_addition

    def products_price(self):
        """Стоимость всей строки (цена * количество)"""
        return self.price_at_addition * self.quantity 


class RedisCartStorage:
    """Техническое хранилище: отвечает за чистую работу с JSON внутри памяти Redis"""
    def __init__(self, session_key):
        # Сохраняем session_key  self.anon_key для Редиса по которму будут храниться данные анонима
        self.anon_key = f"anon_cart:{session_key}"
        # Время жизни корзины анонима — 30 дней в секундах
        self.ttl = 2592000

    def _get_items(self):
        """Внутренний метод: чтение списка словарей из Redis"""
        # cart_data - Запрос в Redis о передаче данных корзины анонима, если нет None. 
        cart_data = cache.get(self.anon_key)
        # Конвертируется из json в dict понятный для python. Если не None.
        return json.loads(cart_data) if cart_data else []
    
    def _save_items(self, items):
        """Внутренний метод: запись списка словарей в Redis с TTL"""
        # Сохранение товаров по  session_key на 30 дней для анонима.
        cache.set(self.anon_key, json.dumps(items), timeout=self.ttl)

    def load_items(self):
        """Склеивает сухие данные из Redis с живыми объектами Product за 1 SQL-запрос"""
        # Данные товаров анонима
        items_data = self._get_items()

        # Быстрый сбор всех ID из корзины Redis
        product_ids = [i['product_id'] for i in items_data]

        # Одним SQL-запросом вытягиваем продукты из PostgreSQL (Защита от N+1)
        # __in - За счет этого мы обратились сразу к всем product_ids одним запросом вместо нескольких.
        # Итог словарь product_id: productn - обьект
        products_dict = {p.id: p for p in Product.objects.filter(id__in=product_ids)}

        # Собираем список понятных объектов-обёрток
        anon_items = []
        for i in items_data:
            p_id = i['product_id']
            if p_id in products_dict:
                # Подготовка к отправке аргументов в RedisAnonCartItem  наш виртуальный класс для анонимов
                # Создали экземпляр класса обьект с данными product, quantity, price_at_addition'
                anon_items.append(RedisAnonCartItem(products_dict[p_id], i['quantity'], i['price_at_addition']))
        # Отправка product, quantity, price_at_addition'
        return anon_items
    
    def change_quantity(self, product_id, quantity_change, price=None, max_quantity= None):
        """Универсальный метод: добавляет, прибавляет или 
        уменьшает количество товара в Redis"""
        # Данные товаров анонима из Redis в словаре
        items = self._get_items()
        # Если совпадений не будет отработает последний else
        for item in items:
            # Проверяем если в корзине Redis такой товар?
            if item['product_id'] == product_id:
                # Меняем кличество товара в строке.
                new_qty = item['quantity'] + quantity_change

                # Проверка остатков на складе (если ограничение передано)
                if max_quantity is not None and new_qty > max_quantity:
                    return
                if new_qty > 0:
                    item['quantity'] = new_qty
                else:
                    items.remove(item)          # Если количество упало до 0 — удаляем товар
                break
        else:
            # Если товара не было в корзине — создаем новую запись
            if quantity_change > 0 and price is not None:
                items.append({'product_id': product_id, 'quantity': quantity_change, 'price_at_addition': price})

        self._save_items(items)

    def remove(self, product_id_delete):
        """Полностью вырезает товар из списка в Redis"""
        items = [i for i in self._get_items() if i['product_id'] != product_id_delete]
        self._save_items(items)

    def clear(self):
        """Полное уничтожение гостевой корзины из Redis"""
        cache.delete(self.anon_key)


class CartService:
    """Высокоуровневый Диспетчер: направляет 
    команды либо в PostgreSQL, либо в RedisStorage"""
    def __init__(self, request):
        self.request = request
        self.user = request.user

        # Сохраняем session_key в Redis - идендификация анонима
        if not self.request.user.is_authenticated:
            if not self.request.session.session_key:
                request.session.create()
            self.redis_storage = RedisCartStorage(request.session.session_key)

    def get_items(self):
        """
        Возвращает список товаров корзины.
        Для авторизованных — реальный QuerySet из PostgreSQL.
        Для анонимов — список товаров в нашем виртуальном RedisAnonCartItem из Redis.
        """
        if self.request.user.is_authenticated:
            cart = Cart.objects.filter(user=self.user).first()
            return cart.cartitem_set.all().select_related('product') if cart else []
        # Анонимы
        return self.redis_storage.load_items()
    
    def total_price(self):
        """Суммарная стоимость всей корзины в целых рублях"""
        return sum(item.products_price() for item in self.get_items)
    
    def total_quantity(self):
        """Суммарное количество всех товаров в корзине"""
        return sum(item.quantity for item in self.get_items())

    def add_item(self, product_id, quantity=1):
        """Добавляет товар в корзину (в БД или в Redis) с заморозкой цены sell_price"""
        # Id - товара
        product = Product.objects.filter(id=product_id)
        final_price = product.sell_price()

        if self.user.is_authenticated:
            # Получаем или создаем корзину по пользователю
            cart, _ = Cart.objects.get_or_create(user=self.user)

            # Получаем товар из конкретной корзины по id - товара 
            # а если не чего получать то создаем строку товара 
            # по заданным аргументам defaults применться в случае создания 
            item, created = CartItem.objects.get_or_create(
                cart=cart, product_id=product_id,
                defaults={'price_at_addition': final_price, 'quantity': quantity} 
            )
            if not created:
                item.quantity += quantity
                item.save()
        else:
            # Сохраняем изменения товара в хранилище Redis
            self.redis_storage.change_quantity(product_id, quantity_change=quantity, price=final_price)

    def update_quantity(self, product_id, operation):
        """Изменяет количество товара (+1/-1) в БД или Redis с контролем остатков склада"""
        product = Product.objects.get(id=product_id)
        change = 1 if operation == 'plus' else -1

        # 1. Логика для авторизованных пользователей в PostgreSQL (Оптимизированная)
        if self.user.is_authenticated:
            item = CartItem.objects.filter(cart__user=self.user, product_id=product_id).first()
            if item:
                # Если увеличить то проверяем остаток в бд
                if change == 1 and item.quantity + 1 <= product.quantity:
                    item.quantity += 1
                    item.save()
                elif change == -1:
                    item.quantity -= 1
                    if item.quantity > 0:
                        item.save()
                    else: 
                        item.delete()

         # 2. Логика для анонимов в Redis
        else:
            # Сохраняем изменения товара в хранилище Redis
            self.redis_storage.change_quantity(product_id, quantity_change=change, max_quantity=product.quantity)

    def remove_item(self, product_id_delete):
        """Полное удаление выбранной позиции из корзины"""
        if self.user.is_authenticated:
            Cart.objects.filter(user=self.user).first().cartitem_set.filter(product_id=product_id_delete).delete()
        else:
            self.redis_storage.remove(product_id_delete)

    def merge_guest_cart(self, guest_session_key):
        """Переносит товары гостя из Redis в PostgreSQL при успешной авторизации"""
        # Если у гостя не было корзины в Redis ИЛИ 
        # пользователь не залогинен — сливать нечего, выходим
        if not guest_session_key or not self.user.is_authenticated:
            return
        
       # Создаем пульт-контейнер для прямого управления корзиной анонима в Redis
        guest_storage = RedisCartStorage(guest_session_key)

        # Загружаем товары гостя: не просто сырые ID, 
        # а список объектов RedisAnonCartItem с живыми продуктами внутри (Защита от N+1)
        guest_items = guest_storage.load_items()

        if not guest_items:
            return
        # Транзакция она убережет данные и бд от обрыва данных 
        # в случае сбоев при записи данных либо запишется все либо не чего.
        with transaction.atomic():
            # Получили или создали корзину пользователя.
            user_cart, _ = Cart.objects.get_or_create(user=self.user)
            # Python начинает по очереди доставать из нашего 
            # гостевого мешка Redis строки товаров анонима
            for item in guest_items:
                # Товары гостя привязываются к корзине пользоваетля если они есть то суммируется 
                # количесвто если нет то создается и полностью записывается 
                # Так как load_items вернул объекты двойники, данные берем ЧЕРЕЗ ТОЧКУ
                cart_item, created = CartItem.objects.get_or_create(
                    cart=user_cart, product_id=item.product.id,
                    defaults={'price_at_addition': item.price_at_addition,
                              'quantity': item.quantity}
                )
                if not created:
                    # Товары одинаковые сумируем.
                    cart_item.quantity += item.quantity
                    cart_item.save()
            guest_storage.clear()
    
    def delete_cart(self):
        """Полное выжигание корзины (для вызова при успешном оформлении заказа)"""
        if self.user.is_authenticated:
            Cart.objects.filter(user=self.user).delete()
        else:
            self.redis_storage.clear()



