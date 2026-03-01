from django.contrib import admin
from goods.models import Category, Product




#admin.site.register(Category)
#admin.site.register(Product)


class ProductInline(admin.TabularInline):
    model = Product
    extra =  1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # Слаг будет сам печататься из названия
    prepopulated_fields = {'slug': ('name',)}
     # Подключаем список товаров
    inlines = [ProductInline]

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Слаг будет сам печататься из названия
    prepopulated_fields = {'slug': ('name',)}  
    
    # Отображение товаров в админ панели.
    list_display = ['name', 'category', 'slug', 
                    'description', 'price', 'quantity', 
                    'discount', 'created_at', 'updated_at',
                    ]

    # Клик и переход по 'name', 'category'
    list_display_links = ('name', 'category',)