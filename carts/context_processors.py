
from django.http import HttpRequest
from carts.services import CartService

def cart_stats(request:HttpRequest):
    """
    Глобальный процессор контекста: поставляет общее количество и сумму 
    товаров в корзине на абсолютно любую страницу сайта (Highload-версия)
    """
    # Если просмотр корзины или бот не шевелимся.
    if not request.user.is_authenticated and not request.COOKIES.get('guest_token'):
        return {
            'total_quantity': 0,
            'total_price': 0,
        }
    # Получаем корзину владельца
    if request.user.is_authenticated:
        cart_service = CartService(user_id=request.user.id)
    else:
        cart_service = CartService(guest_token=request.COOKIES.get('guest_token'))

    # Возвращаем быстрые методы благодаря _cache_items 
    return {
            'total_quantity': cart_service.total_quantity(),
            'total_price': cart_service.total_price(),
        }

   

    



    
