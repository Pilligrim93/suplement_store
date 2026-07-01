from django.urls import path

from users import views

app_name = 'users'

urlpatterns = [
    path("login/", views.MyLoginView.as_view(), name="login"),                              # Вход
    path("registration/", views.UserRegistrationView.as_view(), name="registration"),       # Регистрация
    path("logout/", views.logout, name="logout"),                                           # Выход
    path("profile/", views.UserProfileView.as_view(), name="profile"),

    
]



