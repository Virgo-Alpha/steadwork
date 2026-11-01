from django.conf import settings


def test_api_base_path_is_configured():
    assert settings.ROOT_API_PATH == "/api/"


def test_django_orm_is_disabled_and_tests_select_the_memory_store():
    assert settings.DATABASES["default"]["ENGINE"] == "django.db.backends.dummy"
    assert settings.STORE_BACKEND == "inmemory"
    assert settings.DATABASE_URL.startswith("sqlite:///")

