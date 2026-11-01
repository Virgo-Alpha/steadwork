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

Resource routers, domain models, storage and authentication are separate
modules. Seed data and resource endpoints are intentionally out of scope for
this bootstrap.
