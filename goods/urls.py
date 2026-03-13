
from django.urls import path

from . import views


app_name = 'goods'

urlpatterns = [
    path("", views.shop, name="shop"),
    path("product/<slug:slug>", views.shop_single, name="shop_single"),
    # path("product/<int:product_id>", views.shop_single, name="shop_single"),
    # path("shop-single/", views.shop_single, name="shop_single"),
    path("cart/", views.cart, name="cart"),
    path("checkout/", views.checkout, name="checkout"),
    path("thankyou/", views.thankyou, name="thankyou"),
]

