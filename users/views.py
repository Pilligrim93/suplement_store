# LoginView этот класс написан специально для стандартных задач по авторизации
from email import message

from django.contrib.auth.views import LoginView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.contrib import auth
from django.contrib import messages

from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import UserRegistrationForm



class MyLoginView(LoginView):
    """Авторизация пользоваетля"""

    template_name = 'users/login.html'
    next_page = reverse_lazy('home:index')

    def get(self, request, *args, **kwargs):
        # Если запрос от HTMX — отдаем только саму форму (фрагмент)
        if request.headers.get('HX-Request'):
            return render(request, 'users/includes/_login_form.html')
        # Если обычный заход по ссылке — отдаем всю страницу
        return super().get(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('home:index')
    

    def form_invalid(self, form):
        if self.request.headers.get('HX-Request'):
            # Возвращаем только фрагмент формы с ошибками "Неверный логин или пароль"
            return render(self.request, 'users/includes/_login_form.html', {'form': form})
        return super().form_invalid(form)
    


def logout(request:HttpRequest):
    auth.logout(request)
    return redirect("home:index")



# Мы наследуемся от CreateView. Этот "робот" сам умеет создавать записи в базе данных.
class UserRegistrationView(CreateView):
    """Регистрация пользователя"""

    # Переопределяем переменные из CreateView

    # Указываем, какую форму использовать. Из неё Django узнает, какие поля (email, логин) нужны.
    form_class = UserRegistrationForm

    # Главный "скелет" страницы. Он загрузится, если мы просто перейдем по ссылке в браузере.
    template_name = 'users/login.html'

    # Ссылка для перенаправления после успешной регистрации.
    # reverse_lazy позволяет найти путь по имени 'home:index', даже если проект еще не до конца загружен.
    success_url = reverse_lazy('home:index')

    # Этот метод срабатывает, когда кто-то просто переходит на страницу (GET-запрос)
    def get(self, request, *args, **kwargs):
        # Проверяем: пришел запрос от HTMX (нажата кнопка) или это обычный заход на страницу?
        if request.headers.get('HX-Request'):
            # Если это HTMX, нам не нужна вся страница. Мы отдаем только "начинку" — фрагмент формы.
            # self.get_form() создает объект пустой формы, указанной в form_class выше.
            return render(request, 'users/includes/_registration_form.html', {'form': self.get_form()})
        
        # Если это НЕ HTMX, говорим родителю (CreateView): "Работай как обычно, покажи полную страницу".
        return super().get(request, *args, **kwargs)
    

    def form_valid(self, form):
        # Создаем user и заполняем проверенные данные из form в бд.
        user = form.save()
        # Автоматический авторизируем user.
        auth.login(self.request, user)
        messages.success(self.request, "Успешная регистрация!")

        # 3. МАГИЯ HTMX: Если запрос от HTMX, делаем жесткий редирект всей страницы
        if self.request.headers.get('HX-Request'):
            response = HttpResponse()
            response['HX-Redirect'] = str(self.success_url)
            return response

        
        # Для обычных запросов оставляем стандарт
        return super().form_valid(form)


    # Если это НЕ HTMX, говорим родителю (CreateView): "Работай как обычно, покажи полную страницу".
    def form_invalid(self, form):
        # Снова проверяем: если форму отправили через HTMX (без перезагрузки)
        if self.request.headers.get('HX-Request'):
            # Мы возвращаем ТОЛЬКО фрагмент формы, но теперь внутри объекта 'form' уже лежат ошибки.
            # Благодаря этому пользователь увидит красные надписи под полями мгновенно.
            return render(self.request, 'users/includes/_registration_form.html', {'form': form})

        # Если вдруг HTMX не сработал, отдаем стандартный ответ Django с перезагрузкой страницы.
        return super().form_invalid(form)

    