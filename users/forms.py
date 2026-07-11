from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model 



class UserRegistrationForm(UserCreationForm):
    # Добавим email, так как в стандартной форме его часто нет
    # это строгий приказ Django: «Не пропускай пользователя дальше, 
    # пока он не введет почту
    
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = get_user_model()                         # Моя модель
        fields = ("username", "email")       # Поля, которые будут в форме


class ProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()        # <-- Теперь форма смотрит в общую модель User
        # Все эти поля теперь лежат в одной таблице, Django их легко найдет!
        fields = ['first_name', 'last_name', 'username', 'email', 'phone_number', 'image']





