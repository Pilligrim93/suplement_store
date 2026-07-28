from django.contrib import messages
from django.shortcuts import redirect, render
from django.http import HttpRequest
from carts.services import CartService


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


def cart_add_or_update(request:HttpRequest):
    """Единый универсальный контроллер 
    для добавления, увеличения и уменьшения товара в ОП"""
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = request.POST.get('quantity', 1)
       

        if product_id:
            product_id = int(product_id)
            quantity = int(quantity)

            cart_service = CartService(request)
            cart_items = cart_service.get_items()

            merged_dict = {int(item['product_id']): item for item in cart_items}
            
            if product_id in merged_dict:
                new_quantity = merged_dict[product_id]['quantity'] + quantity
                if new_quantity <= 0:
                    del merged_dict[product_id]
                else:
                    merged_dict[product_id]['quantity'] = new_quantity
            else:
                if quantity > 0:
                    merged_dict[product_id] = {
                        'product_id': product_id,
                        'quantity': quantity
                    }

            cart_items = list(merged_dict.values())
            cart_service.save_items(cart_items)

            # ЛОГИКА ДЛЯ HTMX
            if request.headers.get('HX-Request'):
                # Вместо редиректа возвращаем ТОЛЬКО фрагмент таблицы
                return render(request, 'carts/includes/included_cart.html', {'cart_items': cart_items})
                
            messages.success(request, "Корзина успешно обновлена!")
    # Если это не HTMX (например, отключен JS), делаем обычный редирект
    return redirect(request.META.get('HTTP_REFERER', 'carts:cart_detail'))


def remove_from_cart(request:HttpRequest):
    """Полное удаление товарной позиции из корзины (с поддержкой HTMX)"""
    if request.method == 'POST':
        product_id = request.POST.get('product_id')

        if product_id:
            product_id = int(product_id)

            cart_service = CartService(request)
            cart_items = cart_service.get_items()

            merged_dict = {int(item['product_id']): item for item in cart_items}
            if product_id in merged_dict:
                del merged_dict[product_id]

            cart_items = list(merged_dict.values())
            cart_service.save_items(cart_items)            

            # Если запрос от HTMX
            if request.headers.get('HX-Request'):
                return render(request, 'carts/includes/included_cart.html', {'cart_items': cart_items})
        
    messages.success(request, "Товар успешно удален из корзины!")
    return redirect(request.META.get('HTTP_REFERER', 'carts:cart_detail'))

        
 # Переписываем этот код на тот что будет работать из redis!