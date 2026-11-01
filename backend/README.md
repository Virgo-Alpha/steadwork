# Steadwork backend

The backend uses **Django 5 and Django REST Framework**. The product
specification confirms React + DRF + PostgreSQL, so this issue resolves the
older Express/Drizzle workspace scaffold in favor of Django/DRF. PostgreSQL
will be introduced in a later persistence task; this skeleton uses Django's
dummy database backend and has no database or external-service requirement.

## Run locally

From `backend/`:

```sh
uv sync
uv run python manage.py runserver
```

The smoke endpoint is `GET http://127.0.0.1:8000/api/health/`.

## Tests and checks

```sh
uv run pytest
uv run python manage.py check
```

Run the HTTP integration matrix with DRF's APIClient:

```sh
uv run pytest api/tests/test_api_integration.py
```

Resource routers, domain models, storage and authentication are separate
modules. The in-memory seed is deterministic: companies `company-acme` and
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
