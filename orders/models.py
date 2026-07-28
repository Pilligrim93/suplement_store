from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from django.contrib.auth import get_user_model
from goods.models import Product 


# class OrderManager(models.Manager):
#     """Кастомный менеджер для ликвидации косяка N+1 запросов"""
#     def get_queryset(self):
#         # select_related сразу подтягивает данные пользователя в ОДИН SQL-запрос
#         return super().get_queryset().select_related('user')
    

# class OrderItemManager(models.Manager):
#     """Кастомный менеджер для ликвидации косяка N+1 запросов 
#     сквозной JOIN всех 4-х таблиц разом"""
#     def get_queryset(self):
#         # select_related может принять несколько полей. 
#         # 4 Потому что 4-я таблица это и есть OrderItem
#         # order__user — сквозной прыжок. Тянет: Товар в чеке -> Чек -> Покупателя + сам Товар
#         return super().get_queryset().select_related('order__user', 'product')  


class Order(models.Model):
    """Общая информация о заказе (Контейнер)"""
    # Варианты выбора для валидации бд страховка от опечатки и удобство

    # Статус заказа.
    STATUS_CHOICES = [
        ('requires_payment', 'Ожидает оплаты'),
        ('paid', 'Оплачен'),
        ('in_delivery', 'В пути / Доставка'),
        ('completed', 'Завершен'),
        ('canceled', 'Отменен'),
    ]

    # Способ вариант выбора оплаты.
    PAYMENT_CHOICES = [
        ('online', 'Онлайн-оплата на сайте'),
        ('cash_on_delivery', 'Оплата при получении (наличные)'),
        ('card_on_delivery', 'Оплата при получении (картой курьеру)'),
    ]
    
    # Настраиваем встроенный валидатор телефона для рынка РФ (11 цифр, может начинаться с +)
    # Просто инструкция для проверки.
    phone_validator = RegexValidator(
        regex=r'^(?:\+7|7|8)\d{10}$',  
        message="Неверный формат телефона. Используйте: +79999999999 или 89999999999"
    )

    # Инфо, кто и когда?
    # get_user_model() - дает нам гибкость если решим использовать стандартного/нестандартного user
    # вообще лучше использовать get_user_model() из за гибкости.
    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, related_name='orders', verbose_name="Покупатель")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    # Валидация данных (номер телефона)
    phone_number = models.CharField(
        max_length=20, 
        validators=[phone_validator],           
        verbose_name="Номер телефона")
    
    # Валидация данных (адрес доставки) 
    delivery_address = models.TextField(
        validators=[MinLengthValidator(10, message="Введите подробный адрес доставки (минимум 10 символов).")],
        verbose_name="Адрес доставки")

    # Способ оплаты, статус и транзакции
    # choices - Список готовых вариантов выбора а так же валидация, 
    # выбери из того что есть или иди на хуй))
    payment_method = models.CharField(max_length=30, choices=PAYMENT_CHOICES, default='online', verbose_name="Способ оплаты")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requires_payment', verbose_name="Статус заказа")
    is_paid = models.BooleanField(default=False, verbose_name="Статус оплаты")

    
    # ПОДКЛЮЧАЕМ НАШ УМНЫЙ МЕНЕДЖЕР:
    # objects = OrderManager()

    class Meta:
        db_table = 'order'
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ('-created_at',)
        
    # Проблема N+1 решена кастомным классом через менеджера.
    def __str__(self):
        return f"Заказ № {self.id} | {self.user.username if self.user else 'Аноним'}"
    

class OrderItem(models.Model):
    """Содержимое заказа (Товары внутри контейнера)"""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name="Заказ")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, verbose_name="Товар")

    # КРИТИЧЕСКИ ВАЖНО: Фиксируем цену и имя на момент покупки!
    product_name = models.CharField(max_length=255, verbose_name="Название товара на момент покупки")
    price = models.PositiveIntegerField(verbose_name="Цена при покупке")
    quantity = models.PositiveIntegerField(default=1,  verbose_name="Количество")

    # Подключаем менеджера.
    # objects = OrderItemManager()

    class Meta:
        db_table = 'order_item'
        verbose_name = 'Проданный товар'
        verbose_name_plural = 'Проданные товары'

    def __str__(self):
        # Проблема N+1 решена кастомным классом через менеджера. 
        return f"Товар {self.product_name} для заказа № {self.order.id}"






