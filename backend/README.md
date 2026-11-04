# Steadwork backend

The backend uses **Django 5 and Django REST Framework** for HTTP routing and
**SQLAlchemy 2.x** behind `api.store` for application data. SQLite is the default local persistent store, and PostgreSQL is available through the repository-root Docker Compose stack. Both use Alembic schema migrations. Django's built-in ORM remains disabled; route
handlers use the existing domain dataclasses through the store boundary.

## Run locally

From `backend/`:

```sh
uv sync
uv run alembic upgrade head
uv run python manage.py runserver
```

Alembic creates the schema in `backend/.local-data/steadwork.sqlite3`; the first
API request seeds deterministic demo data. The ignored local-data directory
must remain untracked. Django startup checks that the database is at the
current Alembic head and fails with an upgrade command if the schema is missing
or outdated. To migrate and run against another SQLite file, set `DATABASE_URL`
for both commands, for example:

```sh
DATABASE_URL=sqlite:////tmp/steadwork.sqlite3 uv run alembic upgrade head
DATABASE_URL=sqlite:////tmp/steadwork.sqlite3 uv run python manage.py runserver
```

SQLite and PostgreSQL URLs are supported. Invalid URLs and unsupported database schemes fail during settings initialization; they never fall back to the in-memory store. The smoke endpoint is `GET http://127.0.0.1:8000/api/health/` and reports the selected store.

Registration, email verification, and password reset use Django's email backend.
In local debug mode, verification/reset links are printed to the backend console.
For a hosted deployment configure `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`,
`EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, and `DEFAULT_FROM_EMAIL`; without SMTP,
registration and reset requests report that mail delivery is unavailable. Set the
same strong `DJANGO_SECRET_KEY` on every backend worker: signed access and one-time
email tokens remain valid across process restarts and workers. Password reset
increments the user's auth version and invalidates existing tokens.

## Tests and checks

```sh
uv run pytest
uv run alembic upgrade head
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

Schema migration commands (run from `backend/`):

```sh
uv run alembic revision --autogenerate -m "describe schema change"
uv run alembic upgrade head
uv run alembic current
uv run pytest -q api/tests/test_migrations.py
```

The migration test suite upgrades empty temporary databases, compares the
resulting schema against SQLAlchemy metadata, repeats the upgrade, inspects the
current revision, and verifies the application rejects an unmigrated database
without creating tables. These tests never use the default local database.

Resource routers, domain models, storage and authentication are separate
modules. SQLAlchemy mappings and generic CRUD repositories live in
`api/orm.py` and `api/repositories.py`; request middleware opens one session
per request, commits successful responses, rolls back failures and closes the
session. SQLite foreign-key enforcement protects references. Existing records
are preserved across backend restarts. The committed Alembic revision creates
all eight current persistence tables and their keys, indexes, and relationships.

The seed is deterministic: companies `company-acme` and
`company-orbit`, eight jobs (`job-platform`, `job-design`,
`job-security`, `job-analytics`, `job-infrastructure`, `job-research`,
`job-devrel`, and `job-accessibility`), and users
`candidate@example.com`, `recruiter@example.com`, and
`admin@example.com`. Demo passwords are respectively
`candidate-password`, `recruiter-password`, and `admin-password`.

`POST /api/auth/login/` returns an opaque, expiring bearer token. Protected
probe routes are available at `/api/protected/{candidate,recruiter,admin}/`
and require the matching role; an optional user ID suffix enforces ownership.
Missing, malformed, invalid, or expired tokens return 401, while valid tokens
without the required role or ownership return 403. Call `api.store.reset_store`
between tests to restore the seed without shared state.


## PostgreSQL with Docker Compose

From the repository root, create a local environment file. Keep the generated password private; `.env` is ignored by Git.

Compose requires `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`; `DJANGO_ALLOWED_HOSTS` is optional. Generate a random local password and write the ignored `.env` file like this:

```sh
cat > .env <<EOF
POSTGRES_DB=steadwork
POSTGRES_USER=steadwork
POSTGRES_PASSWORD=$(openssl rand -hex 24)
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
EOF
docker compose up --build -d
```

Compose builds the root multi-stage `Dockerfile`, then starts only PostgreSQL and the application. The Node build stage runs the Vite production build; the Python runtime stage serves those static files and the `/api/` routes from Django without Node installed. Direct frontend routes such as `/jobs` return the SPA entrypoint, while API routes and missing asset paths remain backend/404 responses. The app waits for PostgreSQL, applies `uv run alembic upgrade head`, then starts Django; its health check verifies the PostgreSQL-backed API is ready. The first API request on an empty database inserts deterministic local demo data once. Existing records are retained.

After building the image, `./scripts/check-container-image.sh` checks that its final stage contains the frontend assets without the build-time uv cache, Node runtime, or backend test/dependency artifacts. Pass a different image name as the first argument when using a custom Compose project name.

```sh
docker compose logs -f app postgres
docker compose down                 # stop and preserve the postgres-data volume
docker compose down -v              # destructive: delete the database volume and all its data
```

The seeded candidate login is `candidate@example.com` / `candidate-password`; recruiter and admin demo accounts are also seeded. These credentials are for local development only and must not be used as production secrets. PostgreSQL credentials are configured in the ignored `.env`; `.env.example` contains only a replacement placeholder.
