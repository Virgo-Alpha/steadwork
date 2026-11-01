from django.conf import settings


def test_api_base_path_is_configured():
    assert settings.ROOT_API_PATH == "/api/"


def test_database_uses_dependency_free_dummy_backend():
    assert settings.DATABASES["default"]["ENGINE"] == "django.db.backends.dummy"

