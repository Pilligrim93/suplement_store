from carts.models import Cart, CartItem 

class CartMergeMixin:
    """Миксин для переноса товаров из гостевой сессии в профиль пользователя"""
    def merge_cart(self, guest_session_key):
        # Если ключа сессии нет (например, куки отключены), 
        # выходим сразу, так как искать нечего.
        if not guest_session_key:
            return

        # 1. Пытаемся найти в базе корзину (объект Cart), 
        # которая привязана к этому временному ключу сессии гостя.
        guest_cart = Cart.objects.filter(session_key=guest_session_key).first()

        # Если корзина гостя не найдена в базе (она пустая), 
        # прерываем выполнение — переносить нечего.
        if not guest_cart:
            return
        
        # 2. Ищем корзину, уже принадлежащую вошедшему пользователю.
        # Если её нет — метод get_or_create создаст новую пустую корзину для него.
        # Теперь у нас есть 'user_cart' как целевая точка переноса.
        user_cart, created = Cart.objects.get_or_create(user=self.request.user)

        # 3. Получаем все товары (CartItem) из старой гостевой корзины.
        guest_items = CartItem.objects.filter(cart=guest_cart)

        for item in guest_items:
            # Для каждого товара гостя проверяем: а нет ли уже такого же товара
            # (тот же product) в основной корзине пользователя?
            existing_item = CartItem.objects.filter(
                cart=user_cart,
                product=item.product
            ).first()

            if existing_item:
                # Если такой товар уже есть у юзера, мы просто прибавляем 
                # количество из гостевой корзины к уже имеющемуся.
                existing_item.quantity += item.quantity
                existing_item.save()
            else:
                # Если такого товара в корзине пользователя еще нет,
                # мы просто меняем "владельца" (привязку к корзине) для этой записи.
                item.cart = user_cart
                item.save()

        # 4. После того как все товары перенесены или удалены, 
        # гостевая корзина (контейнер) становится пустой и больше не нужна.
        # Удаляем её из базы данных.
        guest_cart.delete()




