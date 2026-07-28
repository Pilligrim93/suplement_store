from django.urls import path

from users import views

app_name = 'users'

urlpatterns = [
    path("login/", views.MyLoginView.as_view(), name="login"),                              # Вход
    path("registration/", views.UserRegistrationView.as_view(), name="registration"),       # Регистрация
    path("profile/", views.profile_view, name="profile"),                                   # Профиль
    path("logout/", views.logout, name="logout"),                                           # Выход

    
]



