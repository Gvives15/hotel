from django.apps import AppConfig


class AdministrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.administration'
    def ready(self):
        from . import signals  # noqa: F401
