# Steadwork local development

## Setup

From the repository root, install the frontend and backend dependencies:

```sh
make install
```

`make setup` is an alias for the same operation. The backend uses Django's
dummy database backend, so PostgreSQL or another database is not required.

## Run the services

```sh
make dev
```

This starts the Vite frontend at <http://127.0.0.1:5173> and the Django API at
<http://127.0.0.1:8000/api/health/>. Both processes run in the foreground
through one command. If either process exits, `make dev` stops the other and
returns the exited process's status.

The individual services can also be started with `make frontend` and
`make backend`. Override the ports with Make variables, for example:

```sh
make dev FRONTEND_PORT=5174 BACKEND_PORT=8001
```

The frontend's `VITE_DATA_MODE` environment variable may be set to `mock`
(the default) or `api`. No backend environment variables are required for
local development.

## Logs and shutdown

Development logs are written separately to `.steadwork/logs/frontend.log` and
`.steadwork/logs/backend.log`. Press `Ctrl-C` in the `make dev` terminal, or
run `make stop` from another terminal, to stop both services. `make cleanup`
is an alias for `make stop` and removes the process/status files; logs are
retained for inspection.

## Run the tests

Prepare frontend, backend, and Playwright dependencies, and install the
Chromium browser used by the E2E suite:

```sh
make test-setup
```

The complete test command runs the frontend Vitest suite, the backend pytest
suite, and then the browser E2E suite in order. Each stage prints its name,
stops on failure, and reports which stage failed:

```sh
make test
```

The frontend/backend integration tests start the backend with its resettable
in-memory store, so they do not modify the developer's local database.

To run the frontend and backend suites without Docker or Playwright:

```sh
make test-fast
```

Run just the Compose-backed browser suite with:

```sh
make e2e
```

`make e2e` requires Docker Compose and the seeded local demo account values.
Set `E2E_CANDIDATE_EMAIL`, `E2E_CANDIDATE_PASSWORD`,
`E2E_RECRUITER_EMAIL`, and `E2E_RECRUITER_PASSWORD` in the environment before
running `make test` or `make e2e`. These demo accounts are for local
development only. The E2E harness creates its own Compose project and database
volume, waits for the app and database health checks, and removes only its
project and volume on success, failure, or interruption.
