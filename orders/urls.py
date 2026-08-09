from django.urls import path
from orders.views import OrderCreateView


app_name = 'orders'

# urlpatterns = [
#     # Страница оформления заказа: http://localhost:8000/orders/create-order/
#     path('create-order/', OrderCreateView.as_view(), name='create_order'),
# ]
