from django import template

# Создаем экземпляр библиотеки.
# Через эту переменную Django будет регистрировать наш тег, чтобы увидеть его в HTML
register = template.Library()



# Декоратор который превращает обычную функцию в тег шаблона а так же за счет
# takes_context=True функция видит все что есть.
@register.simple_tag(takes_context=True)
# context = старые данные    **kwargs = новые 
def change_params(context, **kwargs):
    # Копируем обьект 'request' так как оригинальный только для чтения.
    query= context['request'].GET.copy()

    # Обновляем данные из **kwargs о новой странице. 
    for key, value in kwargs.items():
        query[key] = value
    return query.urlencode()

    

