from django.conf import settings
import pytest

from api.database import DatabaseConfigurationError, get_database_url, get_store_backend


def test_api_base_path_is_configured():
    assert settings.ROOT_API_PATH == "/api/"


def test_django_orm_is_disabled_and_tests_select_the_memory_store():
    assert settings.DATABASES["default"]["ENGINE"] == "django.db.backends.dummy"
    assert settings.STORE_BACKEND == "inmemory"
    assert settings.DATABASE_URL.startswith("sqlite:///")


def test_database_url_accepts_postgresql_and_requires_a_database():
    url = "postgresql+psycopg://steadwork:local-only@postgres:5432/steadwork"
    assert get_database_url({"DATABASE_URL": url}) == url
    assert get_database_url({"DATABASE_URL": "postgresql://user:pass@localhost/db"}) == "postgresql+psycopg://user:pass@localhost/db"

    with pytest.raises(DatabaseConfigurationError):
        get_database_url({"DATABASE_URL": "postgresql://postgres/"})


def test_store_backend_accepts_postgresql():
    assert get_store_backend({"STEADWORK_STORE": "postgresql"}) == "postgresql"

