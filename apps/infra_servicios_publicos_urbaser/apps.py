from django.apps import AppConfig


class InfraServiciosPublicosUrbaserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name               = 'apps.infra_servicios_publicos_urbaser'
    verbose_name       = 'Infraestructura Servicios Públicos — Urbaser'

    def ready(self):
        # Importar signals y receivers para registrarlos
        import apps.infra_servicios_publicos_urbaser.signals   # noqa
        import apps.infra_servicios_publicos_urbaser.receivers  # noqa
