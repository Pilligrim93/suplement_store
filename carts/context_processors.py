from django.db.models import Sum
from django.http import HttpRequest
from carts.models import Cart

def cart_stats(request:HttpRequest):

    # Если не авторизирован и нет session_key
    if not request.user.is_authenticated and not request.session.session_key:
        return {'total_quantity': 0, 'total_price': 0}

    # Проверка либо ты user либо session_key.
    lookup = {'user': request.user} if request.user.is_authenticated else {'session_key':request.session.session_key}
    # Получаем корзину по user or session_key и берем самую первую если она там не одна.
    cart = Cart.objects.filter(**lookup).first()

    # Если корзина существует то получааем общее количесвто и цену.
    if cart:
        total_quantity = cart.total_quantity()
        total_price = cart.total_price()
    else:
        total_quantity = 0
        total_price = 0
    # Словарь для данных в шаблон.
    return {
        'total_quantity': total_quantity,
        'total_price' : total_price
    }
    



    
    return {'total_quantity': total_quantity}