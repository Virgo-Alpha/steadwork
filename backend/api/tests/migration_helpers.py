"""Helpers that apply committed migrations to isolated test databases."""

from pathlib import Path

from alembic import command
from alembic.config import Config


BACKEND_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_CONFIG = BACKEND_ROOT / "alembic.ini"


def alembic_config(database_url: str) -> Config:
    config = Config(str(ALEMBIC_CONFIG))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    config.attributes["database_url"] = database_url
    return config


def upgrade_database(database_url: str) -> Config:
    config = alembic_config(database_url)
    command.upgrade(config, "head")
    return config
