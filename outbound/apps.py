from django.apps import AppConfig


class OutboundConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'outbound'
    verbose_name = '手工出库管理'

    def ready(self):
        import outbound.signals  # noqa
