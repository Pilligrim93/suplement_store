from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver


# Наследуемся от AbstractUser, чтобы сохранить 
# стандартный функционал Django (логин, пароль, группы)
class User(AbstractUser):

    class Meta:
        db_table = 'user'
        verbose_name = 'Пользователя'
        verbose_name_plural = 'Пользователи'

    # Метод __str__ говорит Django: "Когда нужно показать юзера текстом, выводи его логин"
    def __str__(self):
        return self.username

    # Переопределяем метод 
    def save(self, *args, **kwargs):
        # 1. Проверяем, новый ли это пользователь
        # У него нет pk-id так как еще не записан в бд а только в форме
        is_created = self.pk is None

        # 2. Сначала сохраняем пользователя в базу (чтобы у него появился ID)
        super().save(*args, **kwargs)

        # 3. Если пользователь новый — создаем ему профиль
        if is_created:
            # Это «костыль» против циклической зависимости
            # Импорт ВНУТРИ метода, чтобы избежать ошибки (чтобы Python "увидел" Profile)
            from .models import Profile
            Profile.objects.create(user=self)


class Profile(models.Model):
    # OneToOneField гарантирует: у 1 пользователя может быть только 1 профиль.
    # related_name='profile' позволит обращаться к профилю через юзера: user.profile
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь'
    )

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
        db_table = 'user_profile'
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return f"Профиль для {self.user.username}"
    
