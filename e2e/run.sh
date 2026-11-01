#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PROJECT_NAME="steadwork-e2e-$$"
E2E_PORT=${E2E_PORT:-$((20000 + ($$ % 40000)))}
POSTGRES_DB="steadwork_e2e_$$"
POSTGRES_USER=steadwork_e2e
POSTGRES_PASSWORD=$(od -An -N24 -tx1 /dev/urandom | tr -d ' \n')
STACK_STARTED=0

compose() {
  docker compose --project-name "$PROJECT_NAME" --project-directory "$ROOT_DIR" \
    -f "$ROOT_DIR/docker-compose.yaml" \
    -f "$ROOT_DIR/e2e/docker-compose.e2e.yaml" "$@"
}

require_value() {
  eval "value=\${$1:-}"
  if [ -z "$value" ]; then
    printf 'Required E2E environment variable is missing: %s\n' "$1" >&2
    exit 2
  fi
}

for variable in E2E_CANDIDATE_EMAIL E2E_CANDIDATE_PASSWORD E2E_RECRUITER_EMAIL E2E_RECRUITER_PASSWORD; do
  require_value "$variable"
done

case "$E2E_PORT" in
  ''|*[!0-9]*) printf 'E2E_PORT must be an integer between 1 and 65535.\n' >&2; exit 2 ;;
esac
if [ "$E2E_PORT" -lt 1 ] || [ "$E2E_PORT" -gt 65535 ]; then
  printf 'E2E_PORT must be an integer between 1 and 65535.\n' >&2
  exit 2
fi

cleanup() {
  status=$?
  trap - EXIT INT TERM
  if [ "$STACK_STARTED" -eq 1 ]; then
    # PROJECT_NAME is generated here and always has the e2e-only prefix.
    case "$PROJECT_NAME" in
      steadwork-e2e-*)
        compose down --volumes --remove-orphans || true
        ;;
      *) printf 'Refusing cleanup of unexpected Compose project: %s\n' "$PROJECT_NAME" >&2 ;;
    esac
  fi
  exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

cd "$ROOT_DIR"
if [ ! -x "$ROOT_DIR/e2e/node_modules/.bin/playwright" ]; then
  printf 'Install E2E dependencies first with: cd e2e && npm ci\n' >&2
  exit 2
fi

export POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD E2E_PORT
export DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
export PLAYWRIGHT_BROWSERS_PATH=${PLAYWRIGHT_BROWSERS_PATH:-$ROOT_DIR/e2e/.cache/ms-playwright}
STACK_STARTED=1
compose up --build --detach --wait --wait-timeout 240
export E2E_BASE_URL="http://127.0.0.1:$E2E_PORT"

cd "$ROOT_DIR/e2e"
./node_modules/.bin/playwright test "$@"
