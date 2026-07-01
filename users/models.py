from django.db import models
from django.contrib.auth.models import AbstractUser

# Наследуемся от AbstractUser, чтобы сохранить 
# стандартный функционал Django (логин, пароль, группы)
class User(AbstractUser):


    # Поля профиля (image и phone_number мы перенесли сюда из модели User)
    image = models.ImageField(
        upload_to='users_image/',
        blank=True,
        null=True,
        verbose_name='Аватар'
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Номер телефона'
    )

    class Meta:
        db_table = 'user'
        verbose_name = 'Пользователя'
        verbose_name_plural = 'Пользователи'

    # Метод __str__ говорит Django: "Когда нужно показать юзера текстом, выводи его логин"
    def __str__(self):
        return self.username



# class Profile(models.Model):

#     # Поля профиля (image и phone_number мы перенесли сюда из модели User)
#     image = models.ImageField(
#         upload_to='users_image/',
#         blank=True,
#         null=True,
#         verbose_name='Аватар'
#     )

#     phone_number = models.CharField(
#         max_length=20,
#         blank=True,
#         null=True,
#         verbose_name='Номер телефона'
#     )

#     class Meta:
#         db_table = 'user'
#         verbose_name = 'Пользователя'
#         verbose_name_plural = 'Пользоваетли'

#     def __str__(self):
#         return self.username
    
