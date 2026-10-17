from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EditorialConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.editorial'
    verbose_name = _('گالری الهام و مقاله‌ها')
