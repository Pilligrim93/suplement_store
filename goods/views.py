from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from goods.models import Product


def shop(request):

    # --- 0. Поиск товаров на сайте ---
    # --- 1. ПРИЕМ ДАННЫХ ИЗ URL ---
    # request.GET — это словарь со всеми параметрами после знака "?" в ссылке.
    query = request.GET.get('q')           # Текст поиска (из инпута q) то что ищет пользователь.
    min_p = request.GET.get('min_price')   # Минимальная цена (из JS-слайдера)
    max_p = request.GET.get('max_price')   # Максимальная цена (из JS-слайдера)
    sort_key = request.GET.get('sort')     # Код сортировки (из ссылок в выпадающем списке)

    # --- 2. БАЗОВЫЙ ЗАПРОС ---
    # Начинаем строить запрос к БД. Сразу отсекаем товары, которых нет на складе.
    products = Product.objects.filter(quantity__gt=0)

    # --- 3. ЛОГИКА ПОИСКА ---
    if query:
        # Если пользователь что-то ввел, ищем это слово в трех полях (ИЛИ через Q)
        # distinct() нужен, чтобы товар не дублировался, если слово нашлось сразу в двух местах
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) | 
            Q(category__name__icontains=query)
        ).distinct()

    # --- 4. ГИБКАЯ ФИЛЬТРАЦИЯ ПО ЦЕНЕ ---
    # Создаем временный словарь для условий, чтобы не писать кучу if/else в фильтре
    price_filters = {}
    if min_p: 
        price_filters['price__gte'] = min_p  # gte = "больше или равно"
    if max_p: 
        price_filters['price__lte'] = max_p  # lte = "меньше или равно"
    
    # Распаковываем словарь (**). Если min_p и max_p есть, получится .filter(price__gte=..., price__lte=...)
    products = products.filter(**price_filters)

    # --- 5. УПРАВЛЕНИЕ СОРТИРОВКОЙ ---
    # Список для HTML: ключ (для URL) и красивое название (для пользователя)
    sort_options = {
        'id': 'Relevance',
        'name_asc': 'Name, A to Z',
        'name_desc': 'Name, Z to A',
        'price_low': 'Price, low to high',
        'price_high': 'Price, high to low',
    }
    
    # "Переводчик" для БД: превращаем ключ из URL в реальное поле таблицы
    # Минус перед полем (например, '-price') означает сортировку по убыванию
    sort_map = {
        'name_asc': 'name', 
        'name_desc': '-name',
        'price_low': 'price', 
        'price_high': '-price',
    }
    
    # Берем значение из карты. Если в URL пришел мусор или пусто — по умолчанию ставим 'id'
    order_field = sort_map.get(sort_key, 'id')
    # Итоговый поиск отфильтрованных товаров.
    products = products.order_by(order_field)

    # --- 6. ПАГИНАЦИЯ ---
    # Режем финальный отфильтрованный список на страницы по 12 товаров
    paginator = Paginator(products, 9)
    # Получаем номер текущей страницы и берем нужные товары
    page_obj = paginator.get_page(request.GET.get("page"))

    # --- 7. ОТПРАВКА В ШАБЛОН ---
    return render(request, "goods/shop.html", {
        'products': page_obj,                   # Список товаров для отображения
        'sort_options': sort_options,           # Словарь для создания ссылок в меню через цикл
    })

    

def shop_single(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, "goods/shop-single.html", {'product': product})


def checkout(request):
    return render(request, "checkout.html")


def thankyou(request):
    return render(request, "thankyou.html")
