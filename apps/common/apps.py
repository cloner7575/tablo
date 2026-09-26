from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.common"
    label = "common"
    verbose_name = "Common"

    def ready(self) -> None:
        # Ensure unicode slug converter is registered before URL reversing.
        import apps.common.converters  # noqa: F401
