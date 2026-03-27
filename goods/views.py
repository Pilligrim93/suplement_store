from unicodedata import category

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from goods.models import Product



def shop(request):
    # Получаем текст из инпута поиска
    query = request.GET.get('q')   
    
    if query:
        # Фильтруем по имени, описанию или категории. 
        # icontains делает поиск регистронезависимым.
        products = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) | 
            Q(category__name__icontains=query)
        ).order_by('id').distinct()               # Обязательно для стабильной пагинации
    
    else:
        # Если поиска нет, берем все товары, также сортируя их.
        products = Product.objects.all().order_by('id')

    # Создаем пагинатор: берем наш QuerySet и режем по 6 объектов
    paginator = Paginator(products, 6)

    # Вытаскиваем номер страницы из URL (например, ?page=2)
    page_number = request.GET.get("page")
    # get_page — безопасный метод: вернет 1-ю страницу, если в page_number прилетит мусор
    page_obj = paginator.get_page(page_number)

    context = {
        'products': page_obj        # Оставляем имя 'products', чтобы не переделывать цикл в шаблоне
    }
    
    return render(request, "shop.html", context)


    # # Получаем текст из инпута поиска
    # query = request.GET.get('q')   
    # if query:
    #     # Фильтруем: имя содержит query ИЛИ описание содержит query
    #     products = Product.objects.filter(
    #         Q(name__icontains=query) | Q(description__icontains=query) | 
    #         Q(category__name__icontains=query)
    #     )
    
    # else:
    #     products = Product.objects.all()


    # context = {
    #     'products': products
    # }
    # return render(request, "shop.html", context)



def shop_single(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, "shop-single.html", {'product': product})


# def shop_single(request, product_id):
#     product = get_object_or_404(Product, id=product_id)
#     return render(request, "shop-single.html", {'product': product})

def cart(request):
    return render(request, "cart.html")



def checkout(request):
    return render(request, "checkout.html")


def thankyou(request):
    return render(request, "thankyou.html")
