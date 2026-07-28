from django.db import models
from django.utils.translation import gettext_lazy as _


class Category(models.Model):

    name = models.CharField(max_length=255, unique=True, verbose_name=_('Название'))
    slug = models.SlugField(max_length=255, unique=True, verbose_name=_('Слаг'))

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        db_index=True,
        verbose_name='Родительская категория'
    )


    class Meta:
        verbose_name = _('Категорию') 
        verbose_name_plural = _('Категории')

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} -> {self.name}"
        return self.name

class Product(models.Model):
    
    name = models.CharField(max_length=200, unique=True, verbose_name=_('Название'))
    slug = models.SlugField(max_length=200, unique=True, null=True, verbose_name=_('Слаг'))
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name=_('Категория'))
    description = models.TextField(verbose_name=_('Описание'))
    price = models.PositiveIntegerField(verbose_name=_('Цена'))
    quantity = models.PositiveIntegerField(default=0, db_index=True, verbose_name=_('Количество'))
    image = models.ImageField(upload_to='goods_images/', verbose_name=_('Изображение'))
    discount = models.PositiveIntegerField(default=0, verbose_name=_('Скидка'))
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата добавления заказа'),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата изменения товара'),
    )
    
        
    class Meta:
        verbose_name = _('Продукт') 
        verbose_name_plural = _('Продукты')

    def __str__(self):
        return self.name

    
    def sell_price(self):
        """Чистая цена 1 товара с учетом скидки если она есть"""
        if self.discount and self.discount < self.price:
            return self.price - self.discount
        return self.price