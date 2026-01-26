from django.apps import AppConfig


class XcmsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'xcsm'

    def ready(self):
        import xcsm.signals
