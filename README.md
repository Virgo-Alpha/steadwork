# Steadwork Tech Job Board

Steadwork is a responsive job board for technology job seekers, hiring companies and recruiters, public visitors, and platform administrators. Candidates can discover openings, save jobs, apply and follow application status; employers can publish and manage jobs and review applicants; public visitors can browse jobs and companies. Administrators are an intended product role, but their platform moderation and management capabilities are deferred and unimplemented. This repository contains a working MVP and its contributor workflow.

For the deployed sites, see below:
- Development: https://steadwork-development.onrender.com/
- Production: https://steadwork-production.onrender.com/

## Seeded demo accounts

| Name | Email | Password |
|---|---|---|
| Demo Candidate | `candidate@example.com` | `candidate-password` |
| Demo Recruiter | `recruiter@example.com` | `recruiter-password` |
| Demo Admin | `admin@example.com` | `admin-password` |

Use these accounts only for local development. The Render development and
production services currently share a database, and an empty database is seeded
with these same accounts. Do not use the demo credentials in production.

## Project specifications

The implemented API contract consumed by the frontend is documented in [`openapi.yaml`](openapi.yaml). Product goals and the proposed broader product scope are in [product specifications](_docs/specs.md) and [project scope and decisions](_docs/job_board_project_scope.md). Backend architecture and unresolved decisions are in the [backend plan](_docs/backend-plan.md).

Work is tracked as GitHub issues in the [public issue tracker](https://github.com/Virgo-Alpha/steadwork/issues). The [delivery process](_docs/process.md) describes grooming, dependencies, worktrees, review and status transitions. 

Current API behavior includes public job and company reads; bearer-token login; candidate profile, saved jobs and application flows; employer job and applicant workflows; and in-app notifications. Guest internal applications are accepted. Registration immediately signs users in without sending email. Email verification and password reset are disabled; users who forget a password need operator assistance. Recommendations, CV binary upload/storage, company profile/team administration, platform administrator dashboards and moderation, external-apply tracking and email delivery are not implemented in the API. The mock may demonstrate UI behavior beyond the backend; its sample CV names are not uploaded files. No automatic fallback from API failures to mock data occurs.

## Local setup and commands

Requirements: Node.js/npm for the frontend, Python and [uv](https://docs.astral.sh/uv/) for the backend, and Docker Compose for local observability and the browser suite. From the repository root:

```sh
make run
```

`make run` runs `make install`, applies the local SQLite migrations, starts the self-hosted observability Compose project, Vite and instrumented Django, then waits for the app health checks. Open <http://127.0.0.1:5173>; the API is at <http://127.0.0.1:8000/api/> and Grafana is at <http://127.0.0.1:3000>. The first start creates `observability/.env` with a random local Grafana password. Stop with Ctrl-C or `make stop`; telemetry data remains in named volumes. To install dependencies without starting the app, run `make install`; to start already-installed services, run `make dev`. Ports can be changed with `make run FRONTEND_PORT=5174 BACKEND_PORT=8001`.

## Agent team and process

The PM defines checkable scope ([PM guidance](_docs/team/pm.md)); the software engineer implements one groomed issue ([engineering guidance](_docs/team/software-engineer.md)); QA verifies the acceptance criteria and reports a verdict ([QA guidance](_docs/team/qa-engineer.md)). The orchestrator coordinates tracks and a separate reviewer reviews completed work. See the [local task backlog](_docs/tasks.md) for the tracked work.

## Application 
### Frontend

The frontend is a React 19 and Vite application in `frontend/`. It includes public job search and detail, company pages, candidate and employer views, and sign-in/application flows. The service interface is in `frontend/src/services/job-board-service.ts`; `frontend/src/services/http-job-board-service.ts` is the API client. API mode is the default. Set `VITE_DATA_MODE=mock` to use the browser-storage demo service. Vite proxies `/api` to `http://localhost:8000` by default; override with `API_PROXY_TARGET` when needed. API mode requires a running backend and does not silently switch to mock mode on errors.

### Backend

The backend uses Django 5 and Django REST Framework for HTTP routing, SQLAlchemy 2.x for application data, and Alembic for migrations. The API runs at `/api/`; `GET /api/health/` reports service and datastore health. The frontend-facing endpoints, schemas and authentication requirements are listed in [`openapi.yaml`](openapi.yaml). The backend also has role-protected diagnostic probe routes which are not part of the frontend API contract.

Login returns an expiring bearer token. Protected client requests send it in the `Authorization` header. Demo users are seeded locally on first request to an empty database; see [backend/README.md](backend/README.md) for local demo account details. Never use those demo accounts in production.

### Database

Local backend development uses a persistent SQLite database at `backend/.local-data/steadwork.sqlite3`. Schema changes are applied with Alembic; see the migration commands in the [backend guide](backend/README.md). This is a real local database, not a dummy or automatically reset store. `STEADWORK_STORE=inmemory` is intended for tests and diagnostics. The Compose stack uses PostgreSQL 17 with a persistent named volume. SQLite and PostgreSQL are the supported configured stores.

## Testing
Install all test dependencies, including Playwright Chromium, with `make test-setup`. Run the complete suites in order (frontend Vitest including live API integration, backend pytest, then isolated Compose-backed Playwright E2E) with:

```sh
make test
```

For frontend and backend checks without Docker/Playwright, run `make test-fast`. To run only the browser suite, run `make e2e`; it requires Docker Compose and defaults to the seeded demo accounts documented in the backend guide. Set `E2E_CANDIDATE_EMAIL`, `E2E_CANDIDATE_PASSWORD`, `E2E_RECRUITER_EMAIL`, and `E2E_RECRUITER_PASSWORD` to override them. CI supplies these values as secrets. The E2E harness creates a uniquely named Compose project and database volume and removes that isolated project and volume when it exits. It does not target the normal root Compose project.

## Containerization

The root [`docker-compose.yaml`](docker-compose.yaml) defines two services: `postgres` and `app`. The app image builds the frontend and serves its static files and Django API together on port 8000. Compose waits for PostgreSQL, applies migrations at app startup, seeds demo data on its first API request, and checks the API health endpoint. Compose requires `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` in `.env`; `DJANGO_ALLOWED_HOSTS` is optional. See the [backend guide](backend/README.md) for database setup and migration details. Create the ignored `.env` from `.env.example`, replacing its password placeholder with a locally generated value, then run:

```sh
cp .env.example .env
# Edit .env and replace POSTGRES_PASSWORD with a private random value.
make compose-up
docker compose --project-name steadwork logs -f app postgres
```

`make compose-up` starts the separate observability project and the app/PostgreSQL project together. `make compose-down` stops both and preserves their volumes. To delete persistent data, remove volumes explicitly with `docker compose --project-name steadwork down -v` and `docker compose --project-name steadwork-observability --env-file observability/.env --file observability/compose.yaml down -v`. Keep both `.env` files private; they are ignored by Git. Compose is also used by the isolated browser E2E harness.

## Deployment

Render is managed with Terraform. After all CI tests pass, GitHub Actions publishes a timestamped GHCR image and deploys it to development. Manual production promotion defaults to the latest image that passed the dev health check; supply `IMAGE_TAG=YYYYMMDD-HHMMSS-shortsha` only for a rollback. Production remains gated by GitHub Environment approval. See the [deployment guide](_docs/deployment.md) for setup, secrets, retention, and Terraform teardown commands.

## CI/CD

<img width="1900" height="963" alt="image" src="https://github.com/user-attachments/assets/bad0a33f-47ea-4ac9-b777-d336c16b226d" />


### GitHub Actions

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on pull requests, pushes to `main`, and manual `workflow_dispatch`. Frontend and backend test jobs run in parallel. Full validation then checks Compose configuration, builds the app image, installs dependencies and runs `make test`. The full validation job needs the four E2E Actions secrets named above; on fork pull requests it is skipped because repository secrets are unavailable, while the parallel frontend and backend jobs still run. A successful push to `main` then builds a tagged image and deploys it to Render development. Production promotion is handled by [the manual deployment workflow](.github/workflows/deploy-prod.yml) after the protected `production` GitHub Environment approves it. See the [deployment guide](_docs/deployment.md) for the required secrets/variables and setup.

<img width="1899" height="463" alt="image" src="https://github.com/user-attachments/assets/35752a8c-ebf0-4e8c-af76-208b73b70c8c" />

## Observability

The backend exports OpenTelemetry request and business activity metrics, traces and correlated action logs through Alloy into the self-hosted Prometheus, Tempo and Loki stores. `make run`/`make dev` start that stack automatically with local development; `make compose-up` starts it alongside the containerized app. See the [observability guide](_docs/observability.md) for metric definitions, where to inspect telemetry, trace/log navigation, and how to exercise the local alert.

<img width="848" height="352" alt="bd1811ce-b404-4c3c-ac2a-f338909c95c0_1830x760" src="https://github.com/user-attachments/assets/ee3e774d-72ba-454d-98a7-e98aff5e7112" />

The deployed Render service is not currently configured to export telemetry. A Grafana Cloud OTLP connection is documented as a follow-up assessment in the guide.

## On-call Agent
TODO: Add an agent wakes up on an alert and fixes the issue.
TODO: Document the agent on observability_and_monitoring.md

## Further component guides

- [Frontend guide](frontend/README.md)
- [Backend guide](backend/README.md)
- [API contract](openapi.yaml)
- [Product specifications](_docs/specs.md)
- [Backend plan](_docs/backend-plan.md)
