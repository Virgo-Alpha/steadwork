from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    def ready(self):
        from django.conf import settings

        if settings.STORE_BACKEND != "sqlite":
            return

        # Fail during Django startup when migrations have not been applied.
        # Schema creation belongs to Alembic, never application startup.
        from .repositories import create_database

        engine, _ = create_database(settings.DATABASE_URL)
        engine.dispose()

