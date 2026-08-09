# from django import forms 
# from orders.models import Order

# class CreateOrderForm(forms.ModelForm):
#     """
#     Тонкая форма оформления заказа.
#     Использует системные атрибуты Django 5.2 для автоматической подсветки ошибок.
#     """
#     class Meta:
#         model = Order
#         # Список полей для заполнения клиента.
#         fields = ['phone_number', 'delivery_address', 'payment_method']

#         # Настраиваем внешний вид (виджеты) и подсказки (placeholders) для HTML-вёрстки
#         widgets = {
#             'phone_number' : forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': '+7 (999) 999-99-99',
#                 'type': 'tel',
#             }),
#             'delivery_address': forms.Textarea(attrs={
#                 'class': 'form-control',
#                 'rows': 3,
#                 'placeholder': 'Укажите город, улицу, дом, квартиру...',
#             }),
#             'payment_method': forms.Select(attrs={
#                 'class': 'form-select form-control',                
#             })
#         }


