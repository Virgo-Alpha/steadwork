from logging.config import fileConfig
import os
from pathlib import Path

from sqlalchemy import engine_from_config, event
from sqlalchemy.engine import make_url
from sqlalchemy import pool

from alembic import context
from api.database import get_database_url
from api.orm import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Keep Alembic on the same database selection as the backend. A URL supplied
# programmatically by a test is used unless the process environment overrides it.
database_url = (
    config.attributes.get("database_url")
    or os.environ.get("DATABASE_URL")
    or config.get_main_option("sqlalchemy.url")
    or get_database_url()
)
database_url = get_database_url({"DATABASE_URL": database_url})
config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    url = make_url(config.get_main_option("sqlalchemy.url"))
    if url.drivername in {"sqlite", "sqlite+pysqlite"} and url.database not in {
        None,
        ":memory:",
    }:
        Path(url.database).expanduser().parent.mkdir(parents=True, exist_ok=True)

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={"timeout": 30},
    )

    @event.listens_for(connectable, "connect")
    def enable_sqlite_foreign_keys(connection, _record):
        if connectable.dialect.name != "sqlite":
            return
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
