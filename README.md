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
