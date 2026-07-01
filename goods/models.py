from django.db import models
from django.db.models import F, TextField
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _

# Create your models here.


class Category(models.Model):

    name = models.CharField(max_length=255, unique=True, verbose_name=_('Название'))
    slug = models.SlugField(max_length=255, unique=True, verbose_name=_('Слаг'))

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
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
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name=_('Категория'))
    description = models.TextField(verbose_name=_('Описание'))
    price = models.DecimalField(default=0.00, max_digits=9, decimal_places=2, verbose_name=_('Цена'))
    quantity = models.PositiveIntegerField(default=0, verbose_name=_('Количество'))
    image = models.ImageField(upload_to='goods_images/', verbose_name=_('Изображение'))
    discount = models.DecimalField(default=0.0, max_digits=5, decimal_places=2, verbose_name=_('Скидка'))
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Дата добавления заказа'),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Дата изменения товара'),
    )
    
        

    def __str__(self):
        return self.name


    class Meta:
        verbose_name = _('Продукт') 
        verbose_name_plural = _('Продукты')

    
