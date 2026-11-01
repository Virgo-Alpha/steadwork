"""SQLAlchemy database configuration for the persistent store."""

import os
from pathlib import Path

from sqlalchemy.engine import make_url


class DatabaseConfigurationError(ValueError):
    """Raised when the configured database URL cannot be used here."""


def get_store_backend(environ=None) -> str:
    environ = os.environ if environ is None else environ
    backend = environ.get("STEADWORK_STORE", "sqlite").strip().lower()
    if backend not in {"sqlite", "postgresql", "inmemory"}:
        raise DatabaseConfigurationError("STEADWORK_STORE must be 'sqlite', 'postgresql' or 'inmemory'.")
    return backend


def get_database_url(environ=None) -> str:
    environ = os.environ if environ is None else environ
    default = Path(__file__).resolve().parents[1] / ".local-data" / "steadwork.sqlite3"
    value = environ.get("DATABASE_URL", f"sqlite:///{default}")
    try:
        url = make_url(value)
    except Exception as exc:
        raise DatabaseConfigurationError("DATABASE_URL is not a valid SQLAlchemy URL.") from exc
    if url.drivername not in {"sqlite", "sqlite+pysqlite", "postgresql", "postgresql+psycopg"}:
        raise DatabaseConfigurationError("DATABASE_URL must use SQLite or PostgreSQL.")
    if not url.database:
        raise DatabaseConfigurationError("DATABASE_URL must name a database.")
    if url.drivername == "postgresql":
        value = url.set(drivername="postgresql+psycopg").render_as_string(hide_password=False)
    return value
