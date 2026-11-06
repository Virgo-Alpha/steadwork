"""Migration integration tests for the SQLite schema."""

import os
from pathlib import Path
import subprocess
import sys

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

from api.database import DatabaseConfigurationError, get_database_url
from api.orm import Base
from api.repositories import create_database
from api.tests.migration_helpers import alembic_config


def test_fresh_database_upgrade_matches_all_model_tables_and_constraints(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'fresh.sqlite3'}"
    default_database = Path(get_database_url({}).removeprefix("sqlite:///"))
    default_state = default_database.stat().st_mtime_ns if default_database.exists() else None
    config = alembic_config(database_url)
    head = ScriptDirectory.from_config(config).get_current_head()

    command.upgrade(config, "head")

    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            assert context.get_current_revision() == head
            assert compare_metadata(context, Base.metadata) == []
        tables = set(inspect(engine).get_table_names())
        assert {
            "users", "companies", "jobs", "applications", "candidate_profiles",
            "saved_jobs", "company_memberships", "notifications", "activity_events",
            "alembic_version",
        } <= tables
    finally:
        engine.dispose()

    if default_state is None:
        assert not default_database.exists()
    else:
        assert default_database.stat().st_mtime_ns == default_state


def test_upgrade_is_idempotent_and_current_reports_the_head(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'repeat.sqlite3'}"
    config = alembic_config(database_url)
    head = ScriptDirectory.from_config(config).get_current_head()

    command.upgrade(config, "head")
    first_engine = create_engine(database_url)
    try:
        first_schema = inspect(first_engine)
        first_tables = set(first_schema.get_table_names())
        first_columns = {
            table: [column["name"] for column in first_schema.get_columns(table)]
            for table in first_tables
        }
    finally:
        first_engine.dispose()
    command.upgrade(config, "head")
    command.current(config)

    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            assert MigrationContext.configure(connection).get_current_revision() == head
        after = inspect(engine)
        assert set(after.get_table_names()) == first_tables
        assert {table: [column["name"] for column in after.get_columns(table)] for table in first_tables} == first_columns
    finally:
        engine.dispose()


def test_migration_environment_honors_database_url_override_and_default(monkeypatch, tmp_path):
    override_path = tmp_path / "override-parent" / "override.sqlite3"
    override = f"sqlite:///{override_path}"
    monkeypatch.setenv("DATABASE_URL", override)
    selected_url = get_database_url()
    assert selected_url == override
    config = alembic_config(selected_url)
    assert config.get_main_option("sqlalchemy.url") == override
    command.upgrade(config, "head")
    assert override_path.is_file()

    monkeypatch.delenv("DATABASE_URL")
    default = get_database_url()
    assert default.startswith("sqlite:///")
    assert ".local-data" in default


def test_default_database_upgrade_creates_missing_parent(monkeypatch, tmp_path):
    import api.database

    database_path = tmp_path / "default-parent" / "steadwork.sqlite3"
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(
        api.database,
        "get_database_url",
        lambda environ=None: f"sqlite:///{database_path}",
    )
    config = alembic_config("")
    config.attributes.pop("database_url")
    config.set_main_option("sqlalchemy.url", "")

    command.upgrade(config, "head")

    assert database_path.is_file()


def test_unmigrated_database_fails_with_upgrade_instruction(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'unmigrated.sqlite3'}"
    with pytest.raises(DatabaseConfigurationError, match="alembic upgrade head"):
        create_database(database_url)


def test_django_startup_fails_without_creating_unmigrated_schema(tmp_path):
    database_path = tmp_path / "startup.sqlite3"
    environment = os.environ.copy()
    environment["DATABASE_URL"] = f"sqlite:///{database_path}"
    environment["STEADWORK_STORE"] = "sqlite"
    environment["DJANGO_SETTINGS_MODULE"] = "steadwork.settings"

    result = subprocess.run(
        [sys.executable, "manage.py", "check"],
        cwd=Path(__file__).resolve().parents[2],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "uv run alembic upgrade head" in result.stderr
    assert database_path.exists()
    engine = create_engine(f"sqlite:///{database_path}")
    try:
        assert inspect(engine).get_table_names() == []
    finally:
        engine.dispose()
