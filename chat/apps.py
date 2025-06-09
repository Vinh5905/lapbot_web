from django.apps import AppConfig

class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat'

    def ready(self):
        # Import service ở đây để đảm bảo model được tải khi server khởi động
        from . import predictor_service
        print("Importing predictor service to load ML model...")