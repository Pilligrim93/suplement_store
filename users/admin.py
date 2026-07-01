from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User                       # Моя кастомная модель User


# class ProfileInline(admin.StackedInline):
#     model = Profile                     # Эту модель мы вклеиваем в страницу пользователя.
#     can_delete = False                        #  Запрет на удаление profile в админке если удалить то сайт упаедет.
#     erbose_name_plural = 'Профиль пользователя'


# @admin.register(Profile)
# class ProfileAdmin(admin.ModelAdmin):
#     # Что отображать в списке всех профилей
#     list_display = ('user', 'phone_number', 'image')
    
#     # По каким полям можно искать (поиск по имени пользователя из связанной модели User)
#     search_fields = ('user__username', 'phone_number')



# Регистрируем модель User с использованием стандартных инструментов админки
@admin.register(User)
class MyUserAdmin(UserAdmin):
    # Какие поля отображать в списке пользователей 
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')

    # По каким полям можно искать
    search_fields = ('username', 'email', 'first_name', 'last_name')

    # Поля, которые можно редактировать прямо в списке
    list_editable = ('is_staff',)

    # Добавляем новые поля (телефон и аватар) на страницу редактирования пользователя
    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('phone_number', 'image')
        }),
    )
