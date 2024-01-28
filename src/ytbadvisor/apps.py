from django.apps import AppConfig


class YtbadvisorConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ytbadvisor"

    def ready(self) -> None:
        import ytbadvisor.signals