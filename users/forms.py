from django import forms
from django.contrib.auth.forms import UserCreationForm
from users.models import User   # Моя модель 

class UserRegistrationForm(UserCreationForm):
    # Добавим email, так как в стандартной форме его часто нет
    # это строгий приказ Django: «Не пропускай пользователя дальше, 
    # пока он не введет почту
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User    # Моя модель
        fields = ("username", "email")       # Поля, которые будут в форме