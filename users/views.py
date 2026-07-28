from django.contrib.auth.views import LoginView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import auth
from django.contrib import messages
from django.views.generic import CreateView
from django.urls import reverse_lazy

from carts.services import CartService
from .forms import ProfileForm, UserRegistrationForm


class MyLoginView(LoginView):
    """Авторизация клиента"""
    template_name = 'users/login.html'
    next_page = reverse_lazy('home:index')

    def get(self, request, *args, **kwargs):
        if request.headers.get('HX-Request'):
            return render(request, 'users/includes/_login_form.html')
        return super().get(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('home:index')
    
    def form_valid(self, form):
        anonymous_session_key = self.request.session.session_key        
        response = super().form_valid(form)                     # Просто передали форму родителю она нам не нужна.
        cart_service = CartService(self.request)
        cart_service.merge_guest_cart(anonymous_session_key)                            

        if self.request.headers.get('HX-Request'):
            # Создаем ответ пакет для HTMX куда кладем перенаправление пользователя
            response = HttpResponse()
            response['HX-Redirect'] = str(self.get_success_url())
            return response
        return redirect(self.get_success_url())
    
    def form_invalid(self, form):
        if self.request.headers.get('HX-Request'):
            return render(self.request, 'users/includes/_login_form.html', {'form': form})
        return super().form_invalid(form)
    

class UserRegistrationView(CreateView):
    """Регистрация клиента"""
    form_class = UserRegistrationForm
    template_name = 'users/login.html'
    success_url = reverse_lazy('home:index')

    def get(self, request, *args, **kwargs):
        if request.headers.get('HX-Request'):
            # self.get_form() - это обьект form нужен для работы HTMX
            return render(request, 'users/includes/_registration_form.html', {'form': self.get_form()})
        return super().get(request, *args, **kwargs)
    
    def form_valid(self, form):
        anonymous_session_key = self.request.session.session_key
        user = form.save()
        auth.login(self.request, user)

        cart_service = CartService(self.request)
        cart_service.merge_guest_cart(anonymous_session_key) 

        messages.success(self.request, "Успешная регистрация!")

        if self.request.headers.get('HX-Request'):
            response = HttpResponse()
            response['HX-Redirect'] = str(self.success_url)
            return response
        return redirect(self.success_url)

    def form_invalid(self, form):
        if self.request.headers.get('HX-Request'):
            return render(self.request, 'users/includes/_registration_form.html', {'form': form})
        return super().form_invalid(form)


@login_required    # Защита от не санкцианированого доступа к профилю пользователя это единственная защита.
def profile_view(request: HttpRequest) -> HttpResponse:
    """Создаем профиль"""
    tab = request.GET.get('tab', 'profile')                         # Действие профиль или другие вкладки
    is_edit = request.GET.get('edit') == '1'                       # Редактируем или нет

    if request.method == 'POST':
        form = ProfileForm(data=request.POST, instance=request.user)        # Новые данные от пользовптеля так как редактируем
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль успешно обновлен")
            is_edit = False
        else:
            is_edit = True
    else:
        form = ProfileForm(instance=request.user)                          # Старые данные пользоваетля вывод в полях

    # Если не редактирем то блокируем поля они видны но недоступных пока не нажать редактиоовать
    if not is_edit:
        for field in form.fields.values():
            field.disabled = True

    context = {
        'form': form,
        'tab': tab,                     
        'is_edit': is_edit
    }

    if request.headers.get('HX-Request'):
        return render(request, 'users/includes/_profile_form.html', context)
    return render(request, 'users/profile.html', context)


def logout(request: HttpRequest):
    """Выход из аккаунта"""
    auth.logout(request)
    return redirect("home:index")


    


    










































# LoginView этот класс написан специально для стандартных задач по авторизации
# from email import message

# from django.contrib.auth.views import LoginView
# from django.http import HttpRequest, HttpResponse
# from django.shortcuts import render, redirect
# from django.contrib.auth.decorators import login_required
# from django.contrib.auth.mixins import LoginRequiredMixin
# from django.contrib.auth import get_user_model
# from django.contrib import auth

# from django.contrib import messages

# from django.views.generic import CreateView, UpdateView
# from django.urls import reverse_lazy

# from carts.utils import CartMergeMixin
# from .forms import ProfileForm, UserRegistrationForm



# class MyLoginView(CartMergeMixin, LoginView):
#     """Авторизация пользоваетля"""

#     template_name = 'users/login.html'
#     next_page = reverse_lazy('home:index')

#     def get(self, request, *args, **kwargs):
#         # Если запрос от HTMX — отдаем только саму форму (фрагмент)
#         if request.headers.get('HX-Request'):
#             return render(request, 'users/includes/_login_form.html')
#         # Если обычный заход по ссылке — отдаем всю страницу
#         return super().get(request, *args, **kwargs)
    
#     def get_success_url(self):
#         return reverse_lazy('home:index')
    
#     def form_valid(self, form):
#         # ШАГ 1: Запоминаем анонимный ключ ДО логина
#         anonymous_session_key = self.request.session.session_key

#         # 2. Сначала даем Django выполнить стандартный вход (сессии и т.д.)
#         response = super().form_valid(form)

#         # 3. Сливаем (обьединяем) корзины, передавая старый ключ
#         self.merge_cart(anonymous_session_key)

#         # 2. Если это HTMX, даем тот самый "волшебный пендель" для редиректа всей страницы
#         if self.request.headers.get('HX-Request'):
#             response = HttpResponse()
#             response['HX-Redirect'] = str(self.get_success_url())
#             return response
        
#         # 3. Для обычных браузерных запросов
#         return redirect(self.get_success_url())
    

#     def form_invalid(self, form):
#         if self.request.headers.get('HX-Request'):
#             # Возвращаем только фрагмент формы с ошибками "Неверный логин или пароль"
#             return render(self.request, 'users/includes/_login_form.html', {'form': form})
#         return super().form_invalid(form)
    


# def logout(request:HttpRequest):
#     auth.logout(request)
#     return redirect("home:index")



# # Мы наследуемся от CreateView. Этот "робот" сам умеет создавать записи в базе данных.
# class UserRegistrationView(CartMergeMixin, CreateView):
#     """Регистрация пользователя"""

#     # Переопределяем переменные из CreateView

#     # Указываем, какую форму использовать. Из неё Django узнает, какие поля (email, логин) нужны.
#     form_class = UserRegistrationForm

#     # Главный "скелет" страницы. Он загрузится, если мы просто перейдем по ссылке в браузере.
#     template_name = 'users/login.html'

#     # Ссылка для перенаправления после успешной регистрации.
#     # reverse_lazy позволяет найти путь по имени 'home:index', даже если проект еще не до конца загружен.
#     success_url = reverse_lazy('home:index')

#     # Этот метод срабатывает, когда кто-то просто переходит на страницу (GET-запрос)
#     def get(self, request, *args, **kwargs):
#         # Проверяем: пришел запрос от HTMX (нажата кнопка) или это обычный заход на страницу?
#         if request.headers.get('HX-Request'):
#             # Если это HTMX, нам не нужна вся страница. Мы отдаем только "начинку" — фрагмент формы.
#             # self.get_form() создает объект пустой формы, указанной в form_class выше.
#             return render(request, 'users/includes/_registration_form.html', {'form': self.get_form()})
        
#         # Если это НЕ HTMX, говорим родителю (CreateView): "Работай как обычно, покажи полную страницу".
#         return super().get(request, *args, **kwargs)
    

#     def form_valid(self, form):

#         anonymous_session_key = self.request.session.session_key

#         # Создаем user и заполняем проверенные данные из form в бд.
#         user = form.save()

#         # Автоматический авторизируем user.
#         auth.login(self.request, user)

#         # Привязываем корзину к пользователю
#         self.merge_cart( anonymous_session_key) 

#         messages.success(self.request, "Успешная регистрация!")

#         # 3. МАГИЯ HTMX: Если запрос от HTMX, делаем жесткий редирект всей страницы
#         if self.request.headers.get('HX-Request'):
#             response = HttpResponse()
#             response['HX-Redirect'] = str(self.success_url)
#             return response

        
#         # Для обычных запросов оставляем стандарт
#         return redirect(self.success_url)


#     # Если это НЕ HTMX, говорим родителю (CreateView): "Работай как обычно, покажи полную страницу".
#     def form_invalid(self, form):
#         # Снова проверяем: если форму отправили через HTMX (без перезагрузки)
#         if self.request.headers.get('HX-Request'):
#             # Мы возвращаем ТОЛЬКО фрагмент формы, но теперь внутри объекта 'form' уже лежат ошибки.
#             # Благодаря этому пользователь увидит красные надписи под полями мгновенно.
#             return render(self.request, 'users/includes/_registration_form.html', {'form': form})

#         # Если вдруг HTMX не сработал, отдаем стандартный ответ Django с перезагрузкой страницы.
#         return super().form_invalid(form)

    
# class UserProfileView(LoginRequiredMixin, UpdateView):
#     """Личный кабинет пользователя с гарантированной блокировкой полей через бэк"""
#     # Переопределяем переменные под себя.
#     model = get_user_model()
#     form_class = ProfileForm
#     template_name = 'users/profile.html'
#     success_url = reverse_lazy('users:profile')

#     def get_object(self, queryset=None):
#         """Возвращает текущего пользователя"""
#         return self.request.user

#     def get_form(self, form_class=None):
#         """Этот метод собирает форму для ВСЕХ сценариев (и F5, и HTMX)"""
#         form = super().get_form(form_class)
        
#         # Проверяем, хочет ли пользователь редактировать прямо сейчас
#         is_edit = self.request.GET.get('edit') == '1'
        
#         # Если форма пришла с ошибками (после POST), она ДОЛЖНА быть открыта
#         if self.request.method == 'POST' and not form.is_valid():
#             is_edit = True

#         # ЕСЛИ НЕ РЕДАКТИРУЕМ — БЛОКИРУЕМ ВСЕ ПОЛЯ НА КОРНЮ
#         if not is_edit:
#             for field in form.fields.values():
#                 field.disabled = True
                
#         return form

#     def get(self, request, *args, **kwargs):
#         self.object = self.get_object()
        
#         # Если это скрытый клик от HTMX — отдаем только внутренний шаблон
#         if request.headers.get('HX-Request'):
#             tab = request.GET.get('tab', 'profile')
#             is_edit = request.GET.get('edit') == '1'
            
#             context = self.get_context_data()
#             context['tab'] = tab
#             context['is_edit'] = is_edit
#             return render(request, 'users/includes/_profile_form.html', context)
        
#         # Обычный холодный заход (F5) — отдаем всю страницу целиком.
#         # Метод get_form() отработает сам внутри super() и заблокирует поля!
#         return super().get(request, *args, **kwargs)

#     def post(self, request, *args, **kwargs):
#         self.object = self.get_object()
#         form = self.get_form()
#         if form.is_valid():
#             return self.form_valid(form)
#         return self.form_invalid(form)
        
#     def form_valid(self, form):
#         response = super().form_valid(form)
#         if self.request.headers.get('HX-Request'):
#             messages.success(self.request, "Профиль успешно обновлен")
#             return render(self.request, 'users/includes/_profile_form.html', self.get_context_data())
#         return response
    
#     def form_invalid(self, form):
#         if self.request.headers.get('HX-Request'):
#             return render(self.request, 'users/includes/_profile_form.html', {'form': form})
#         return super().form_invalid(form)














    
# class UserProfileView(LoginRequiredMixin, UpdateView):
#     """Личный кабинет пользователя на классах с поддержкой HTMX"""

#     # Переопределяю переменные super()

#     # Получаю свою кастомную модель User 
#     model = get_user_model()

#     # Получаю форму.
#     form_class = ProfileForm

#     # Указываю главный шаблон личного кабинета.
#     template_name = 'users/profile.html'

#     # Куда перенаправить при успешном сохранении (на эту же страницу)
#     success_url = reverse_lazy('users:profile')


#     # Переопределяя этот метод мы отключаем 
#     # стандартный поиск по id из url
#     def get_object(self, queryset=None):
#         """Получаем текущего user из request"""
#         # Возвращаем текущего пользователя в UpdateView. 
#         return self.request.user
    

#     def get(self, request, *args, **kwargs):

#         # Текущий экземпляр класса становиться конкретным текущим User
#         self.object = self.get_object()
        
#         # 1. Считываем маркеры из URL (работает и для HTMX, и для обычной ссылки)
#         # Что выбрал пользователь данные в этих перерменных.
#         tab = request.GET.get('tab')
#         is_edit = request.GET.get('edit') == '1'

#         # 2. Собираем контекст и дописываем маркеры
#         context = self.get_context_data()
#         context['tab'] = tab
#         context['edit_mode'] = is_edit

#         # 3. ЛОГИКА БЭКЕНДА: Если НЕ режим редактирования — блокируем ВСЕ поля
#         if not is_edit:
#             for field in context['form'].fields.values():
#                 field.disabled = True

#         # 4. Диспетчер ответов:
#         if request.headers.get('HX-Request'):
#             # Если кликнул HTMX — отдаем только начинку
#             return render(request, 'users/includes/_profile_form.html', context)
        
#         # Если это первый заход на страницу — отдаем весь profile.html, 
#         # но передаем туда наш настроенный context!
#         return super().get(request, *args, **kwargs)

    

#     # def get(self, request, *args, **kwargs):

#     #     # Текущий экземпляр класса становиться конкретным текущим User
#     #     self.object = self.get_object()
        
#     #     # Если запрос от HTMX
#     #     if request.headers.get('HX-Request'):
#     #         # Получаем переменную из template где будут заказы или профиль 
#     #         tab = request.GET.get('tab')
#     #         if tab == 'orders':
#     #             # 3-е аргументы содержат данные для template.
#     #             return render(request, 'users/includes/_user_orders.html', {'user': request.user})
#     #         if tab == 'profile':
#     #             return render(request, 'users/includes/_profile_form.html', self.get_context_data())
#     #     # Загрузка всей страницы profile.htmx. 
#     #     # Переменные *args, **kwargs попадают из url
#     #     return super().get(request, *args, **kwargs)
    

#     def post(self, request, *args, **kwargs):

#         # Текущий экземпляр класса становиться конкретным текущим User
#         self.object = self.get_object()
#         # Данные формы
#         form = self.get_form()
#         if form.is_valid():
#             # Если допустимая сохранем в бд и уведомляем user о успехе. 
#             return self.form_valid(form)
#         # Иначе не сохраняем но выводим форму с ошибками для user. 
#         return self.form_invalid(form)
        
#     def form_valid(self, form):
#         # Важно это сохраняет форму пользоваетля а не просто 
#         # подготовка ответа если запрос не от HTMX. 
#         response = super().form_valid(form)

#         if self.request.headers.get('HX-Request'):
#             messages.success(self.request, "Профиль успешно обновлен")
#             return render(self.request, 'users/includes/_profile_form.html', {'form': form})
#         return response
    
#     def form_invalid(self, form):
#         # response = super().form_invalid(form) - не используем так
#         #  как здесь сохранение формы не нужно
#         if self.request.headers.get('HX-Request'):
#             return render(self.request, 'users/includes/_profile_form.html', {'form': form})
#         # Возвращаем форму с ошибками для пользователя.
#         return super().form_invalid(form)
