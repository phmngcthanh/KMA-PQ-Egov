from django.apps import AppConfig


class PkiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pki'
    verbose_name = 'Public Key Infrastructure'

    def ready(self):
        # Import signals if needed
        pass
