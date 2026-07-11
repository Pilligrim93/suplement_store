
import uuid

from django.shortcuts import render 

from django.urls import reverse_lazy
from django.views.generic import CreateView

from orders.forms import CreateOrderForm
from orders.models import Order
from carts.models import Cart


class OrderCreateView(CreateView):
    """
    Контроллер для отображения страницы оформления заказа.
    Доступен всем: и авторизованным пользователям, и анонимам.
    """
    # Переопределили переменные для работы CreateView
    model = Order
    form_class = CreateOrderForm
    template_name = 'orders/create_order.html'

    # Куда перенаправим при успехе (пока заглушка на главную магазина)
    success_url = reverse_lazy('goods:index')

    def get_context_data(self, **kwargs) :
        """Передаем элементы существующей корзины"""

        # CreateView делиться с нами данными
        context = super().get_context_data(**kwargs)
        request = self.request

        # === ДОБАВЛЯЕМ СВЕЖИЙ КЛЮЧ ПРИ ПЕРВОЙ ЗАГРУЗКЕ СТРАНИЦЫ ===
        #context['idempotency_key'] = str(uuid.uuid4())


        # 1. Поиск корзины user or session_key
        if request.user.is_authenticated:
            lookup_filter = {'user': request.user}
        else:
            # Если у анонима есть ключ сессии, ищем по нему. Если нет — фильтр будет пустым
            session_key = request.session.session_key
            lookup_filter = {'session_key': session_key} if session_key else None

        # 2. Ищем корзину только если фильтр успешно сформирован
        cart = None
        if lookup_filter:
            cart = Cart.objects.filter(**lookup_filter).prefetch_related('cartitem_set__product').first()
        
        # Заполняем данные context корзиной для страницы
        context['cart'] = cart

        # 3. Кладем данные в контекст страницы
        if cart:
            # Решена проблема N+1, кладем в context данные содержимое корзины.
            context['cart_items'] = cart.cartitem_set.all().select_related('product')
        else:
            # Кладем в context данные содержимое корзины.
            context['cart_items'] = []
        # Возвращаем напичканый данными context для использования в html
        return context
    
    def form_invalid(self, form):
        """
        Вызывается автоматически, если форма или модель завалили проверку.
        Возвращает ИСКЛЮЧИТЕЛЬНО легкий фрагмент формы через стандартный render.
        """
        #idempotency_key = str(uuid.uuid4())

        # Если запрос пришел от HTMX, рендерим ИСКЛЮЧИТЕЛЬНО блок формы
        if self.request.headers.get('HX-Request'):
            return render(self.request, 'orders/includes/_order_form.html', {'form': form})
            
        # Если это старый браузер без HTMX/JS, срабатывает стандартная перезагрузка страницы
        return super().form_invalid(form)

    
    def form_valid(self, form):
        """
        Вызывается автоматически, когда ОБА поля заполнены верно.
        Глушит стандартное сохранение CreateView, убирая ошибку 500 в логах!
        """
        if self.request.headers.get('HX-Request'):
            # Просто возвращаем чистый HTML формы без ошибок
            return render(self.request, 'orders/includes/_order_form.html', {'form': form})  
        return super().form_valid(form)