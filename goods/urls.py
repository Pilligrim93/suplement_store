
from django.urls import path

from . import views


app_name = 'goods'

urlpatterns = [
    path("", views.shop, name="shop"),
    path("product/<slug:slug>", views.shop_single, name="shop_single"),         # Добавил slug для удобства чтения в адресной сроке вместо product/2
    #path("cart/", views.cart, name="cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("thankyou/", views.thankyou, name="thankyou"),
]

