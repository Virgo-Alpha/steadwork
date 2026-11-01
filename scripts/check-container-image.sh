#!/usr/bin/env sh
set -eu

image=${1:-steadwork-app:latest}
docker run --rm --user 0 --entrypoint /bin/sh "$image" -ec '
  test ! -e /root/.cache/uv
  test ! -e /tmp/uv-cache
  test ! -d /app/backend/api/tests
  test ! -d /app/backend/.venv
  test ! -d /app/backend/node_modules
  test -d /opt/steadwork/frontend/assets
  if command -v node >/dev/null 2>&1; then
    echo "unexpected Node runtime in final image" >&2
    exit 1
  fi
  echo "Final image has built frontend assets and no uv cache, test suite, virtualenv, node_modules, or Node runtime."
'
