"""SQLAlchemy database configuration for the persistent store."""

import os
from pathlib import Path

from sqlalchemy.engine import make_url


class DatabaseConfigurationError(ValueError):
    """Raised when the configured database URL cannot be used here."""


def get_store_backend(environ=None) -> str:
    environ = os.environ if environ is None else environ
    backend = environ.get("STEADWORK_STORE", "sqlite").strip().lower()
    if backend not in {"sqlite", "inmemory"}:
        raise DatabaseConfigurationError("STEADWORK_STORE must be 'sqlite' or 'inmemory'.")
    return backend


def get_database_url(environ=None) -> str:
    environ = os.environ if environ is None else environ
    default = Path(__file__).resolve().parents[1] / ".local-data" / "steadwork.sqlite3"
    value = environ.get("DATABASE_URL", f"sqlite:///{default}")
    try:
        url = make_url(value)
    except Exception as exc:
        raise DatabaseConfigurationError("DATABASE_URL is not a valid SQLAlchemy URL.") from exc
    if url.drivername not in {"sqlite", "sqlite+pysqlite"}:
        raise DatabaseConfigurationError("Only SQLite DATABASE_URL values are supported by this backend.")
    if url.database is None:
        raise DatabaseConfigurationError("DATABASE_URL must name a SQLite database file or :memory:.")
    return value
