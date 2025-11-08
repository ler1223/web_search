from django.apps import AppConfig
from .model_manager import clip_manager


class SearchServiceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "search_service"

    def ready(self):
        # Предзагружаем модель при запуске приложения
        clip_manager.load_model()
