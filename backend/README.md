# Steadwork backend

The backend uses **Django 5 and Django REST Framework** for HTTP routing and
**SQLAlchemy 2.x** behind `api.store` for application data. SQLite is the
default persistent store. PostgreSQL and schema migrations are separate future
tasks. Django's built-in ORM remains disabled; route handlers use the existing
domain dataclasses through the store boundary.

## Run locally

From `backend/`:

```sh
uv sync
uv run python manage.py runserver
```

By default the first API request creates `backend/.local-data/steadwork.sqlite3`
and seeds the deterministic demo data once. The ignored local-data directory
must remain untracked. To use another SQLite file, set `DATABASE_URL` before
starting the server, for example:

```sh
DATABASE_URL=sqlite:////tmp/steadwork.sqlite3 uv run python manage.py runserver
```

Only SQLite URLs are supported in this task. Invalid URLs and unsupported
database schemes fail during settings initialization; they never fall back to
the in-memory store. The smoke endpoint is
`GET http://127.0.0.1:8000/api/health/` and reports `store: sqlite`.

## Tests and checks

```sh
uv run pytest
uv run python manage.py check
```

The unit suite explicitly selects the resettable in-memory backend, so it
does not create or modify the local SQLite file. To use the in-memory backend
outside tests, set `STEADWORK_STORE=inmemory`; this is intended for tests and
local diagnostics, not persistent development data.

Run the HTTP integration matrix with DRF's APIClient:

```sh
uv run pytest api/tests/test_api_integration.py
```

Run the SQLite-backed HTTP integration suite with a fresh temporary database
for every test:

```sh
uv run pytest -q api/tests/test_sqlite_integration.py
```

The suite overrides `DATABASE_URL` with a file under pytest's `tmp_path`, checks
that the developer's default `backend/.local-data/steadwork.sqlite3` is
untouched, then disposes the SQLAlchemy engine and removes the temporary
database and SQLite sidecar files. It can be run repeatedly without leaving a
database in the repository. To run the existing in-memory backend tests
independently of this SQLite suite:

```sh
uv run pytest -q api/tests --ignore=api/tests/test_sqlite_integration.py
```

Pytest loads `steadwork.test_settings`, which explicitly selects the
resettable in-memory store for those existing tests.

Resource routers, domain models, storage and authentication are separate
modules. SQLAlchemy mappings and generic CRUD repositories live in
`api/orm.py` and `api/repositories.py`; request middleware opens one session
per request, commits successful responses, rolls back failures and closes the
session. SQLite foreign-key enforcement protects references. Existing records
are preserved across backend restarts. Schema migration history and upgrade
commands belong to issue #16 and are not included yet.

The seed is deterministic: companies `company-acme` and
`company-orbit`, jobs `job-platform` and `job-design`, and users
`candidate@example.com`, `recruiter@example.com`, and
`admin@example.com`. Demo passwords are respectively
`candidate-password`, `recruiter-password`, and `admin-password`.

`POST /api/auth/login/` returns an opaque, expiring bearer token. Protected
probe routes are available at `/api/protected/{candidate,recruiter,admin}/`
and require the matching role; an optional user ID suffix enforces ownership.
Missing, malformed, invalid, or expired tokens return 401, while valid tokens
without the required role or ownership return 403. Call `api.store.reset_store`
between tests to restore the seed without shared state.
