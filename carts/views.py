from django.contrib import messages
from django.shortcuts import redirect, render
from django.http import HttpRequest
from carts.services import CartService

# Create your views here.

def cart_detail(request:HttpRequest):
    """Просмотр самой корзины и ее товаров"""
    # Создаем обьект - класс для работы с Postgresql и Redis
    cart_service = CartService(request)
    # Товары в корзине
    cart_items = cart_service.get_items()

    # Для отображения и работы товаров в шаблоне.
    context = {
        'cart_items': cart_items,
    }
    # Обычная перезагрузка страницы
    return render(request, 'carts/cart.html', context)


def add_to_cart(request:HttpRequest):
    """Добавление товара в корзину через CartService"""
    if request.method == 'POST':
        # Извлекаем ID из запроса так как в 
        # целях безопасности мы не передаем данные через url
        product_id = request.POST.get('product_id')

        if product_id:
            # Передали запрос для того чтобы класс 
            # понимал что происходит все данные там о событиях
            cart_service = CartService(request)

            # Добавляем товар в один вызов: сервис сам заморозит цену,
            # проверит остатки СУБД или запишет данные анонима в быстрый Redis!
            cart_service.add_item(product_id=int(product_id), quantity=1)

            messages.success(request, "Товар успешно добавлен в корзину!")

    # Возвращаем пользователя обратно на ту страницу, где он был
    return redirect(request.META.get('HTTP_REFERER', 'goods:shop'))


def cart_update(request:HttpRequest):
    """Изменение количества товара (+1/-1) в 
    корзине через CartService (с поддержкой HTMX)"""
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        # Получаем инфу о типе операции + -
        operation = request.POST.get('operation')

        if product_id and operation:
            cart_service = CartService(request)

            # Данные обновяться в Redis или Postgresql
            cart_service.update_quantity(product_id=int(product_id), operation=operation)

            # ЛОГИКА ДЛЯ HTMX
            if request.headers.get('HX-Request'):
                # Получаем обьекты товаров
                cart_items = cart_service.get_items()

                # Вместо редиректа возвращаем ТОЛЬКО фрагмент таблицы
                return render(request, 'carts/includes/included_cart.html', {'cart_items': cart_items})
                    
    # Если это не HTMX (например, отключен JS), делаем обычный редирект
    return redirect(request.META.get('HTTP_REFERER', 'carts:cart_detail'))


def remove_from_cart(request:HttpRequest):
    """Полное удаление товарной позиции из корзины (с поддержкой HTMX)"""
    if request.method == 'POST':
        product_id = request.POST.get('product_id')

        if product_id:
            # Запускаем наш сервис
            cart_service = CartService(request)
            # Удаление в Redis или Postgresql
            cart_service.remove_item(product_id_delete=int(product_id))

            # Если запрос от HTMX
            if request.headers.get('HX-Request'):
                # Получаем обьекты товаров
                cart_items = cart_service.get_items()
                return render(request, 'carts/includes/included_cart.html', {'cart_items': cart_items})
        

    messages.success(request, "Товар успешно удален из корзины!")
    return redirect(request.META.get('HTTP_REFERER', 'carts:cart_detail'))

        
 