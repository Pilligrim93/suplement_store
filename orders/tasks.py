

# from celery import shared_task
# from django.db import transaction
# from django.contrib.auth import get_user_model
# from orders.models import Order, OrderItem
# from goods.models import Product

# @shared_task(name="orders.tasks.tasks_create_order")
# def task_create_order(user_id: int | None, cleaned_data: dict, cart_items_data: list[dict]):
#     """
#     Фоновый воркер Celery для финальной фиксации чека в PostgreSQL.
#     Выполняется асинхронно, полностью разгружая веб-потоки Django.
#     """
#     User = get_user_model()

#     # ШАГ 2: Открываем  ACID-транзакцию на уровне PostgreSQL.
#     # Гарантирует принцип «Всё или ничего»: если запишется Order, но упадут OrderItems,
#     # Postgres сделает автоматический ROLLBACK и полностью зачистит битые данные на диске.
#     with transaction.atomic():

#         # Находим пользователя, если заказ оформлен авторизованным клиентом
#         user_instance = None
#         if user_id:
#             try:
#                 user_instance = User.objects.get(id=user_id)
#             except User.DoesNotExist:
#                 pass        # Если юзера удалили в процессе, оставляем None (сохранится как Аноним)
        
#         # ШАГ 3: Создаем главный контейнер заказа (Один SQL-запрос INSERT)
#         order = Order.objects.create(
#             user=user_instance,
#             phone_number=cleaned_data.get('phone_number'),
#             delivery_address=cleaned_data.get('delivery_address'),
#             payment_method=cleaned_data.get('payment_method', 'online'),
#             status='requires_payment',  # Дефолтный статус из твоей модели
#             is_paid=False
#         )

#         # Подготавливаем пустой список в оперативной памяти воркера для пакетной вставки
#         order_items_to_create = []

#         # Обходим массив корзины, который прилетел в задачу в виде плоского JSON-списка
#         for item_data in cart_items_data:
#             product_id = item_data.get('product_id')

#             # Пытаемся получить живую ссылку на товар для Foreign Key
#             try:
#                 product_instance = Product.objects.get(id=product_id)
#             except Product.DoesNotExist:
#                 # Защита: если товар удалили из каталога, чек не должен упасть
#                 product_instance = None 
        
#             # КРИТИЧЕСКИ ВАЖНО: Намертво фиксируем историческую цену и имя на момент покупки!
#             # Даже если админ изменит цену в каталоге завтра, этот проданный чек не исказится.
#             order_item = OrderItem(
#                 order=order,
#                 product=product_instance,
#                 product_name=item_data.get('product_name'),
#                 price=int(item_data.get('price')),
#                 quantity=int(item_data.get('quantity', 1))
#             )
#             # Просто складываем готовый Python-объект в кучу, не трогая жесткий диск
#             order_items_to_create.append(order_item)

#         # ШАГ 4: HIGHLOAD-РАКЕТА (bulk_create)
#         # Вместо убойного цикла с кучей запросов, упаковываем всю корзину 
#         # в ОДИН-ЕДИНСТВЕННЫЙ мощный пакетный SQL-запрос к PostgreSQL!
#         if order_items_to_create:
#             OrderItem.objects.bulk_create(order_items_to_create)
#         # Возвращаем ID созданного заказа. Celery зафиксирует его в логах успешного выполнения.
#         return order.id
    
    # Проверить tasks эту на баги а так же узнать почему здесь только для авторизированых выполняются операции?????