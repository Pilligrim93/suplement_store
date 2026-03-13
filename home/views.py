from django.http import HttpResponse
from django.shortcuts import render
from goods.models import Product


def index(request):
    # Получаем все товары.
    product = Product.objects.all()

    context = {
        'title': 'Home - Главная страница',
        'products': product,            # Передаем список в шаблон.
    }
    return render(request, 'index.html', context)


def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')