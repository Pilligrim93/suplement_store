from django.contrib import messages
from django.forms import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpRequest
from carts.models import Cart, CartItem
from goods.models import Product

# Create your views here.

def cart_detail(request:HttpRequest):
    """Просмотр самой корзины и ее товаров"""
    
    cart_items = []

    if request.method == 'GET':
        if request.user.is_authenticated:
            # Как вариант привязка по пользователю.
            look_filter = {'user': request.user}
        else:
            # Если в запросе нет ключа сессии. 
            if not request.session.session_key:
                request.session.create()            # Создаем ее.
            # Как вариант привязка по ключу сессии.
            look_filter = {'session_key': request.session.session_key}
        # Расспаковывваем словарь либо пo session_key или user
        # Получаем корзину отфильтрованную по ключу или пользователю и берем первое значение из списка
        cart = Cart.objects.filter(**look_filter).first()

        # Если корзина существует.
        if cart:
            cart_items = cart.cartitem_set.all().select_related('product')
       

    context = {
        'cart_items': cart_items,
    }
    return render(request, 'carts/cart.html', context)


def add_to_cart(request:HttpRequest):

    # POST если изменяем + или - товар.
    if request.method == 'POST':
        # Если пользоваетль авторизирован.
        if request.user.is_authenticated:
            # Либо по пользователю.
            lookup_filter = {'user': request.user}
            
        else:
            # Если нет session_key.
            if not request.session.session_key:

                # Создаем session  а не session_key так как у session_key нет команды create()
                request.session.create()

            # Либо по session_key из session.
            lookup_filter = {'session_key': request.session.session_key}
                
        # Это подставит либо user=..., либо session_key=...
        # Создаем и привязываем корзину по session_key так как пользователь не авторизирован.
        cart, cart_created = Cart.objects.get_or_create(**lookup_filter)

        # Содержимое корзины (товары)  обращаемся через cart так как есть связь 
        # ForeignKey в CartItem
        #cart_items = cart.cartitem_set.all().select_related('product')

        # Выбранный товар (номер товара) для изменения + или -
        product_id = request.POST.get('product_id')

        # Получаем цену продукта, используем 404 что бы сервер не упал если будет 
        # не верный id
        product_price = get_object_or_404(Product, id=product_id).price

        if product_id: 
            product_id = int(product_id)

        # Искомый товар
        item = cart.cartitem_set.filter(product_id=product_id).first()

        
        # Обрабатываем оба варианта есть или нет товара.
        if item:                            # Если товар есть.
            item.quantity += 1              # Добавляем так как товар уже есть в корзине.
            item.save()                 # Сохраняем изменения
            
        else:
            # Создаем новую запись и указываем цену
            #  так как это обязательно при создании товара.
            cart.cartitem_set.create(product_id=product_id, 
                                     quantity=1,
                                     price_at_addition=product_price)

    messages.success(request, "Товар успешно добавлен в корзину!")
    # Возвращаем пользователя обратно на ту страницу где он был,
    # Если не получится вернет в каталог
    return redirect(request.META.get('HTTP_REFERER', 'goods:shop'))


def cart_update(request:HttpRequest):

    if request.method == 'POST':
        if request.user.is_authenticated:
            lookup = {'user': request.user}
        else:
            if not request.session.session_key:
                return redirect(request.META.get('HTTP_REFERER', 'carts:cart_detail'))
            # Если есть ключ сесии.
            lookup = {'session_key': request.session.session_key}

        # Корзина по user or session_key
        cart = Cart.objects.filter(**lookup).first()
         
        product_id = request.POST.get('product_id')

        # Тип операции товара + или - 
        operation = request.POST.get('operation')

        # Сам товар искомый.
        item = cart.cartitem_set.filter(product_id=product_id).first()

        product = get_object_or_404(Product, id=product_id)

        if operation == 'plus' and item.quantity + 1 <= product.quantity:         # Не идеально точная проверка что бы клиент заказал больше чем есть на складе.
            item.quantity += 1
            item.save()
        elif operation == 'minus':
            if item.quantity > 1:
                item.quantity -= 1
                item.save()
            else:
                item.delete()

        # ЛОГИКА ДЛЯ HTMX
        if request.headers.get('HX-Request'):
            # Снова берем товары (уже обновленные в базе)
            cart_items = cart.cartitem_set.all().order_by('id').select_related('product')

            # Вместо редиректа возвращаем ТОЛЬКО фрагмент таблицы
            return render(request, 'carts/includes/included_cart.html', {'cart_items': cart_items})
    # Если это не HTMX (например, отключен JS), делаем обычный редирект
    return redirect(request.META.get('HTTP_REFERER', 'carts:cart_detail'))


def remove_from_cart(request:HttpRequest):

    if request.method == 'POST':
        # 1. Собираем условия поиска корзины
        if request.user.is_authenticated:
            lookup = {'user': request.user}
        else:
            # Если ключа сессии нет, то и корзины точно нет
            if not request.session.session_key:
                return redirect(request.META.get('HTTP_REFERER', 'carts:cart_detail'))
            lookup = {'session_key': request.session.session_key}

        # 2. Ищем корзину (не создаем новую без нужды)
        cart= Cart.objects.filter(**lookup).first()
        
        if cart:
            product_id = request.POST.get('product_id')
            
            if product_id:
                # 3. Безопасное удаление
                cart.cartitem_set.filter(product_id=int(product_id)).delete()
        
        # Если запрос от HTMX
        if request.headers.get('HX-Request'):
            # Корзина с товарами упорядоченная по id.
            cart_items = cart.cartitem_set.all().order_by('id').select_related('product')
            # Возвращаем обновленный фрагмент (товар исчезнет из таблицы мгновенно)
            return render(request, 'carts/includes/included_cart.html', {'cart_items': cart_items})

    messages.success(request, "Товар успешно удален из корзины!")
    return redirect(request.META.get('HTTP_REFERER', 'carts:cart_detail'))

        

