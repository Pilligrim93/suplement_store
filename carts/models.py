from django.conf import settings
from django.db import models
from goods.models import Product

class Cart(models.Model):
    """Эта модель служит контейнером"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,       # Стандартный user от джанго он же потом будет ссылаться на моего.
        on_delete=models.CASCADE, 
        null=True, blank=True           # Анонимный пользователь
    )

    # Дата создания 
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    # Дата обновления
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    
    def total_quantity(self):
        return sum(item.quantity for item in self.cartitem_set.all())
    

class CartItem(models.Model):
    """Содержимое корзины"""

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, verbose_name='Корзина товаров')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Наименование')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество') 
    price_at_addition = models.PositiveIntegerField(verbose_name='Цена при добавлении в корзину')
    active = models.BooleanField(default=True, verbose_name='Статус')

    class Meta:
        ordering = ['id']

    def products_price(self):
        # Умножаем цену товара при добавлении 
        # на количесвто в строке товара.
        return self.price_at_addition * self.quantity


    
        

  

























# from django.db import models
# from goods.models import Product
# from django.contrib.auth import get_user_model

# # Модель пользователя от django я еще свою не создавал.
# User = get_user_model() 

# class Cart(models.Model):

#     # Связь с пользователем (null=True, так как корзина может быть анонимной)
#     user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, verbose_name='Пользователь')

#     # Ключ сессии для анонимных пользователей.
#     session_key = models.CharField(max_length=32, blank=True, null=True, verbose_name='Ключ сессии')

#     # Связь с товаром.
#     product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')

#     # Кол-во товара.
#     quantity = models.PositiveSmallIntegerField(default=0, verbose_name='Количество')

#     # Время добавления.
#     created_timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

#     class Meta:
#         db_table = 'cart'               # Имя таблицы в бд.
#         verbose_name = 'Корзину'
#         verbose_name_plural = 'Корзины'

#     def __str__(self):
#         return f"Корзина {self.user or 'Аноним'} | Товар {self.product.name} | Кол-во {self.quantity} "
    
#     def products_price(self):
#         # Товар * кол-во этого же товара.
#         return int(self.product.price * self.quantity)