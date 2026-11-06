from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    def ready(self):
        from django.conf import settings

        from .telemetry import configure_otlp_logging

        configure_otlp_logging()

        if settings.STORE_BACKEND == "inmemory":
            return

        # Fail during Django startup when migrations have not been applied.
        # Schema creation belongs to Alembic, never application startup.
        from .repositories import create_database
        from .telemetry import configure_business_metrics

        engine, _ = create_database(settings.DATABASE_URL)
        configure_business_metrics(engine)

