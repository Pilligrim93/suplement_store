

# import uuid
# from django.contrib import messages
# from django.shortcuts import redirect, render 

# from django.urls import reverse_lazy
# from django.views.generic import CreateView

# from carts.services import CartService
# from orders.forms import CreateOrderForm
# from orders.models import Order
# from carts.models import Cart


# def create_order_view(request):
#     """
#     Супербыстрый диспетчер оформления заказа (FBV).
#     Полностью контролирует Redis, Lua и Celery, не нагружая PostgreSQL.
#     """
#     cart_service = CartService(request)
#     cart_items = cart_service.get_items()

#     if request.method == "GET":
#         if not cart_items:
#             messages.error(request,"Ваша корзина пуста!")
#             return redirect('carts:cart_detail')

#         form = Create

#         # CreateView делиться с нами данными
#         context = super().get_context_data(**kwargs)
#         request = self.request

#         # Идендификатор события для действия по кнопке оформить заказ
#         context['idempotency_key'] = str(uuid.uuid4())
    
#         cart_service = CartService(request)
#         cart_items = cart_service.get_items()
        
#         context['cart_items'] = cart_items
#         context['total_quantity'] = cart_service.total_quantity()
#         context['total_price'] = cart_service.total_price()

#         return context
    
#     def form_invalid(self, form):
#         """
#         Вызывается автоматически, если форма или модель завалили проверку.
#         Возвращает ИСКЛЮЧИТЕЛЬНО легкий фрагмент формы через стандартный render.
#         """
#         #idempotency_key = str(uuid.uuid4())

#         # Если запрос пришел от HTMX, рендерим ИСКЛЮЧИТЕЛЬНО блок формы
#         if self.request.headers.get('HX-Request'):
#             return render(self.request, 'orders/includes/_order_form.html', {'form': form})
            
#         # Если это старый браузер без HTMX/JS, срабатывает стандартная перезагрузка страницы
#         return super().form_invalid(form)

    
#     def form_valid(self, form):
#         """
#         Вызывается автоматически, когда ОБА поля заполнены верно.
#         Глушит стандартное сохранение CreateView, убирая ошибку 500 в логах!
#         """
#         if self.request.headers.get('HX-Request'):
#             # Просто возвращаем чистый HTML формы без ошибок
#             return render(self.request, 'orders/includes/_order_form.html', {'form': form})  
#         return super().form_valid(form)
    

  



 