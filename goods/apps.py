from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class GoodsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'goods'
    verbose_name = _('Товары')
