from django.urls import path

from . import views

app_name = 'carts'

urlpatterns = [
    path("", views.cart_view, name="cart_view"),
    path("cart-add-or-update/", views.cart_add_or_update, name="cart_add_or_update"),
    path("remove-from-cart/", views.remove_from_cart, name="remove_from_cart"),

]
