import uuid
from django.contrib import messages
from django.shortcuts import redirect, render
from django.http import HttpRequest
from carts.services import CartService


def _get_cart_service(request: HttpRequest):
    """Внутренний хелпер: определяет владельца корзины и ленивый UUID"""
    if request.user.is_authenticated:
        return CartService(user_id=request.user.id), None

    guest_token = request.COOKIES.get("guest_token")
    token = guest_token or str(uuid.uuid4()) 
    return CartService(guest_token=token), token


def cart_view(request: HttpRequest):
    """Просмотр самой корзины и её товаров"""
    if not request.user.is_authenticated and not request.COOKIES.get("guest_token"):
        return render(request, 'carts/cart.html', {'cart_items': []})

    cart_service, token =  _get_cart_service(request)
    response = render(request, 'carts/cart.html', {'cart_items': cart_service.get_items()})

    # httponly=True (Железный щит от XSS-атак и кражи корзин)
    # samesite='Lax' (Защита от CSRF-атак)
    if token:
        response.set_cookie('guest_token', token, max_age=2592000, httponly=True, samesite='Lax')

    return response

def cart_add_or_update(request: HttpRequest):
    """Единый контроллер для добавления и изменения количества товаров."""

    if not (raw_product_id := request.POST.get('product_id')):
        return redirect(request.META.get('HTTP_REFERER', 'carts:cart_view'))

    # try/except защищает от текстового мусора хакеров в POST
    try:
        product_id = int(raw_product_id)
        quantity = int(request.POST.get('quantity', 1))     
    except ValueError:
        return redirect(request.META.get('HTTP_REFERER', 'carts:cart_view'))

    # Предохранитель от холостых кликов (если прилетел 0 — ничего не делаем)
    if quantity == 0:
        return redirect(request.META.get('HTTP_REFERER', 'carts:cart_view'))

    cart_service, token = _get_cart_service(request)
    
    # Провекра на случай отсутствие товара в каталоге
    if not cart_service.add_or_update_item(product_id, quantity):
        messages.error(request, "Товар не существует или удален из каталога!")
        return redirect(request.META.get('HTTP_REFERER', 'carts:cart_view'))

    context = {'cart_items': cart_service.get_items()}
    
    
    if request.headers.get('HX-Request'):
        response = render(request, 'carts/includes/included_cart.html', context)
    else:
        messages.success(request, "Корзина успешно обновлена!")
        response = redirect(request.META.get('HTTP_REFERER', 'carts:cart_view'))

    # Твоё скользящее окно: если это аноним — продлеваем ему куку на 30 дней при КАЖДОЙ активности
    if token:
        response.set_cookie('guest_token', token, max_age=2592000, httponly=True, samesite='Lax')
        
    return response
      
def remove_from_cart(request: HttpRequest):

    # Защита
    if not (raw_product_id := request.POST.get('product_id')):
        return redirect(request.META.get('HTTP_REFERER', 'carts:cart_view'))

    # Защита
    if not request.user.is_authenticated and not request.COOKIES.get("guest_token"):
        return redirect(request.META.get('HTTP_REFERER', 'carts:cart_view'))

    # try/except от падения сервера, если прислали битый ID товара
    try:
        product_id = int(raw_product_id)
    except ValueError:
        return redirect(request.META.get('HTTP_REFERER', 'carts:cart_view'))

    cart_service, token = _get_cart_service(request)
    cart_service.remove_item(product_id)
    context = {'cart_items': cart_service.get_items()}

    if request.headers.get("HX-Request"):
        response = render(request, 'carts/includes/included_cart.html', context)
    else:
        messages.success(request, 'Товар успешно удален из корзины!')
        response = redirect(request.META.get('HTTP_REFERER', 'carts:cart_view'))
        
    if token:
        response.set_cookie('guest_token', token, max_age=2592000, httponly=True, samesite='Lax')

    return response








        









