from django.urls import path

from . import views

app_name = 'carts'

urlpatterns = [
    path("", views.cart_detail, name="cart_detail"),
    path("cart-detail/", views.cart_detail, name="cart_detail"),
    path("add-to-cart/", views.add_to_cart, name="add_to_cart"),
    path("cart-update/", views.cart_update, name="cart_update"),
    path("remove-from-cart/", views.remove_from_cart, name="remove_from_cart"),

]
