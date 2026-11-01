#!/usr/bin/env sh
set -eu

docker compose config --format json | python3 -c '
import json, sys
config = json.load(sys.stdin)
services = config["services"]
assert set(services) == {"app", "postgres"}, set(services)
app, postgres = services["app"], services["postgres"]
assert app["depends_on"]["postgres"]["condition"] == "service_healthy"
assert any(v["target"] == "/var/lib/postgresql/data" for v in postgres["volumes"])
assert "alembic upgrade head" in " ".join(app["command"])
assert "postgres:5432/" in app["environment"]["DATABASE_URL"]
assert app["environment"]["STEADWORK_STORE"] == "postgresql"
assert postgres["healthcheck"] and app["healthcheck"]
'
! git ls-files --error-unmatch .env >/dev/null 2>&1
printf 'Compose defines only app and postgres, with health gating, persistence, and migration startup.\n'
