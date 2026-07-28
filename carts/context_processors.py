
from django.http import HttpRequest
from carts.services import CartService

def cart_stats(request:HttpRequest):
    """
    Глобальный процессор контекста: поставляет общее количество и сумму 
    товаров в корзине на абсолютно любую страницу сайта (Highload-версия)
    """
    # Запустили на сервис 
    cart_service = CartService(request)

    # Вызываем быстрые гибридные методы подсчета (БЕЗ бага N+1 и с поддержкой Redis!
    return {
        'total_quantity': cart_service.total_quantity(),
        'total_price': cart_service.total_price(),
    }
    



    
