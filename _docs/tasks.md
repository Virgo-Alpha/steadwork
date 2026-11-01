# Steadwork backlog

## 1. [Done] Verify the frontend job discovery experience
Goal: Visitors can browse, search, filter, sort and view job details in the responsive frontend.
Description: Confirm the existing job list, search controls, filters, sorting, job detail page and company views against the requirements in `specs.md`. Keep the mock service as the data source and record this frontend slice as complete.

## Acceptance criteria

- [x] The home page displays seeded mock jobs with title, company, location, type and posting information.
- [x] Keyword, location, job type, remote policy, experience, salary and skills filters update the visible results.
- [x] Recent, salary and relevance sorting produce deterministic visible ordering.
- [x] A visitor can open a job detail page and navigate to its company profile.
- [x] Empty results, missing jobs and loading failures show the existing user-facing feedback states.

## Out of scope

- Backend endpoints and persistence, covered by #7.
- Replacing the mock service, covered by #12.

## Constraints

- Keep the existing React and TypeScript structure.
- Do not change the API contract in `openapi.yaml`.
- Use the existing mock service and frontend test conventions.

## 2. [Done] Verify candidate frontend workflows
Goal: Candidates can use the completed frontend flows for profiles, saved jobs, applications and notifications.
Description: Confirm the existing candidate-facing pages and states cover profile editing, saved jobs, application history, application submission, withdrawal and notification behavior described in `specs.md`. Keep these flows on the mock service until the real backend integration task.

## Acceptance criteria

- [x] A candidate can view and edit the supported profile fields.
- [x] A candidate can save and unsave a job and see saved-job availability.
- [x] A candidate can submit an internal application with a selected CV and optional cover letter.
- [x] A candidate can view application history, filter it by status/date, and withdraw an eligible application.
- [x] Notifications show unread state and can be marked read.
- [x] Validation, duplicate-application, unavailable-job and failure states are visible.

## Out of scope

- Backend candidate and application endpoints, covered by #8.
- Frontend/backend HTTP integration, covered by #13.

## Constraints

- Keep mock data mode and existing domain types.
- Follow the responsive React UI patterns already in the frontend.
- Do not add production email or file storage.

## 3. [Done] Verify employer frontend workflows
Goal: Employers can use the completed frontend flows for job management and application review.
Description: Confirm the existing employer-facing pages and states cover dashboard metrics, job creation and management, job lifecycle changes, applicant lists and application status updates. Keep these flows on the mock service until the real backend integration task.

## Acceptance criteria

- [x] An employer dashboard shows active jobs, job counts, application counts and recent applicants.
- [x] An authorized employer can create, edit and view managed jobs.
- [x] Job lifecycle controls visibly support draft, published, closed and expired states where represented by the frontend.
- [x] An employer can view applicants for a job and update an application status.
- [x] Unauthorized, missing-resource and validation failures show visible feedback.

## Out of scope

- Backend employer and notification endpoints, covered by #9.
- Frontend/backend HTTP integration, covered by #13.

## Constraints

- Keep the existing mock service and TypeScript domain models.
- Preserve the API shapes in `openapi.yaml`.
- Do not implement server-side authorization in the frontend.

## 4. [Done] Verify responsive frontend behavior
Goal: The frontend remains usable on desktop, tablet and mobile viewport sizes.
Description: Check the completed responsive layout, navigation, forms, lists, detail pages and feedback states at the supported viewport sizes. Fix or document only frontend issues discovered during this verification; backend behavior remains out of scope.

## Acceptance criteria

- [x] Primary navigation and page content remain usable at desktop, tablet and mobile widths.
- [x] Job lists, filters, detail views, dashboards and forms do not require horizontal scrolling at supported widths.
- [x] Interactive controls remain reachable and visibly indicate loading, error, empty and success states.
- [x] Keyboard focus and readable text contrast are preserved in the verified views.
- [x] Existing frontend tests pass after responsive verification.

## Out of scope

- New product functionality, covered by #2 and #3.
- Backend or container layout, covered by #18.

## Constraints

- Use the existing CSS and component conventions.
- Do not replace the frontend framework or add a new UI library.
- Keep the mock contract stable.

## 5. [Done] Create the backend application skeleton
Goal: A runnable backend service exposes the `/api` base path and has a maintainable structure for implementing the OpenAPI contract.
Description: Choose and document the backend stack consistently with the project architecture decision, resolving the existing Express/Drizzle versus Django/DRF discrepancy before implementation. Create the application entry point, configuration, routers, models, store and test layout, and add a health or equivalent smoke endpoint without introducing a database dependency.

## Acceptance criteria

- [x] The chosen backend stack and the resolution of the Express/Drizzle versus Django/DRF discrepancy are documented.
- [x] The backend starts from a clean checkout using the documented uv commands.
- [x] `/api` is configured as the API base path and a health/smoke endpoint returns a successful response.
- [x] Routers, models, store, auth and tests are separate modules with clear import boundaries.
- [x] Starting the backend does not require a database or external service.
- [x] Unit tests cover configuration and the smoke endpoint.

## Out of scope

- Seeded domain data and bearer authentication, covered by #6.
- Public resource endpoints, covered by #7.

## Constraints

- Use uv for backend dependency management.
- Preserve the paths and JSON conventions in `openapi.yaml`.
- Do not introduce SQLite, PostgreSQL or migrations in this task.

## 6. [Done] Implement the in-memory backend foundation
Goal: The backend serves seeded data from an in-memory store with modular routers, models, authentication and unit tests.
Description: Use an in-memory store and deterministic seed data so the frontend has useful jobs, companies, candidates and applications to display. Split the implementation into routers, models, store and auth modules; add hashed-password authentication and bearer-token authorization for protected endpoints; and write unit tests for the store, authentication and authorization behavior.

## Acceptance criteria

- [x] A fresh backend process creates deterministic seeded companies, jobs, users and representative applications in memory.
- [x] Passwords are stored only as salted one-way hashes and never returned in API responses.
- [x] Login issues a bearer token, and protected endpoints reject missing, malformed and invalid tokens.
- [x] Role and ownership checks distinguish candidate, recruiter/admin and public access.
- [x] The in-memory store can be reset between tests without state leaking between cases.
- [x] Unit tests cover seeding, password verification, token validation and protected-route failures.

## Out of scope

- Resource-specific public endpoints, covered by #7.
- Candidate/application business flows, covered by #8.
- Persistent storage, covered by #14.

## Constraints

- Keep routers, models, store and auth as separate modules.
- Use a test-safe token secret from configuration; never commit secrets.
- Preserve the contract's bearer-token requirement for this backend implementation.

## 7. [Done] Implement the core public job and company API
Goal: Public frontend reads work against the backend for jobs and companies.
Description: Implement the public job list, job detail, company list and company detail endpoints from `openapi.yaml`, including the documented filters, sorting and error behavior. Keep the responses compatible with the existing TypeScript domain types and add unit tests for filtering, sorting, seeded data and missing resources.

## Acceptance criteria

- [x] `GET /api/jobs/` returns only published, non-expired jobs by default.
- [x] Job keyword, location, type, remote policy, experience, company, salary, skills and posted-within filters are applied according to `openapi.yaml`.
- [x] Recent, salary and relevance sorting return deterministic results.
- [x] `GET /api/jobs/{id}/` returns a contract-compatible job or a clear not-found error.
- [x] `GET /api/companies/` and `GET /api/companies/{id}/` return contract-compatible public company data.
- [x] Invalid query values produce a client error rather than silently changing the requested filter.
- [x] Unit tests cover each filter family, sorting, empty results and missing resources.

## Out of scope

- Candidate recommendations, covered by #8.
- Employer job mutations, covered by #9.
- HTTP-level integration coverage, covered by #10.

## Constraints

- Keep response fields compatible with `frontend/src/domain/types.ts` and `openapi.yaml`.
- Public reads must not require authentication.
- Do not add database queries; use the in-memory store from #6.

## 8. [Done] Implement candidate and application API flows
Goal: Candidates and guests can complete the application flows defined by the API contract.
Description: Implement registration/login integration points as needed, candidate profile reads and updates, saved-job management, candidate application listing, registered applications, guest applications and withdrawals. Enforce authentication, candidate ownership, duplicate prevention and lifecycle validation, and add unit tests for successful and rejected cases.

## Acceptance criteria

- [x] Candidate profile GET/PATCH, saved-job GET/POST/DELETE and candidate application listing match the contract.
- [x] Registered candidates can submit one valid internal application per job with a selected CV and optional cover letter.
- [x] Guests can submit the required guest application fields without receiving candidate-only access.
- [x] Candidates can withdraw an eligible application, cannot reapply after withdrawal, and submitted applications cannot be edited.
- [x] Duplicate candidate and guest-email applications are rejected with a client-visible error.
- [x] Applications to closed or expired jobs are rejected, while external-only jobs record an `External click` application according to the contract.
- [x] Unit tests cover successful flows, validation, ownership, duplicates and lifecycle failures.

## Out of scope

- Employer application review and status changes, covered by #9.
- CV binary upload storage, covered by a future API extension after #22.
- HTTP-level integration coverage, covered by #10.

## Constraints

- Use the auth and in-memory store modules from #6.
- Preserve the request/response shapes in `openapi.yaml`.
- Do not add a database dependency.

## 9. [Done] Implement employer and notification API flows
Goal: Employers can manage jobs and applications, and users can read and update notifications.
Description: Implement employer dashboard, managed job CRUD/status operations, employer application listing/status updates, notification listing and notification read operations. Enforce company membership and role permissions, preserve the contract's response shapes, and add unit tests for ownership, permissions and status transitions.

## Acceptance criteria

- [x] Employer dashboard returns the documented job, application, status and recent-applicant metrics.
- [x] Company admins and recruiters can create or update only jobs belonging to their company.
- [x] Job status transitions enforce valid lifecycle and deadline rules.
- [x] Authorized employer users can list applications for their jobs and update allowed application statuses.
- [x] Candidates can list their notifications and mark their own notifications read.
- [x] Users cannot read or mutate another company’s jobs, applicants or notifications.
- [x] Unit tests cover permissions, ownership, invalid transitions and notification read state.

## Out of scope

- Email delivery and asynchronous retries, covered by a future notification delivery issue.
- Team invitations and membership administration, covered by a future company-management issue.
- HTTP-level integration coverage, covered by #10.

## Constraints

- Use the auth, models and in-memory store modules from #6.
- Preserve the API contract and existing frontend domain types.
- Do not implement an admin dashboard or database persistence here.

## 10. [Done] Add backend API integration tests
Goal: The backend contract works through HTTP across its major public, candidate and employer flows.
Description: Add integration tests that start the backend with the seeded in-memory store and exercise representative requests through the HTTP layer. Cover authentication, public reads, candidate applications, employer operations, notifications, validation and protected-route failures, while keeping tests independent and repeatable.

## Acceptance criteria

- [x] Tests start an isolated backend app with deterministic in-memory data.
- [x] Tests cover public jobs/companies, login and at least one protected candidate and employer flow.
- [x] Tests cover guest application, duplicate rejection, invalid lifecycle requests and unauthorized access.
- [x] Tests assert status codes and important response fields from `openapi.yaml`.
- [x] Tests reset state between cases and pass in a clean process without a database.
- [x] The backend integration test command is documented.

## Out of scope

- Frontend-to-backend browser integration, covered by #13.
- SQLite persistence tests, covered by #15.

## Constraints

- Test through HTTP rather than calling router functions directly.
- Use the existing backend test runner and uv commands.
- Do not require Docker or external services.

## 11. [Done] Add a single-command local development Makefile
Goal: One command starts the frontend and backend together for local development.
Description: Create a Makefile with clear targets for installing or preparing dependencies, starting the frontend, starting the backend and starting both services concurrently. Document required environment variables, ports and how to stop the processes, and ensure the command works from a clean checkout without a database.

## Acceptance criteria

- [x] `make dev` starts both frontend and backend processes with the documented ports.
- [x] Separate `make frontend`, `make backend`, install/setup and stop or cleanup targets are available.
- [x] A clean checkout can prepare dependencies and start without a database.
- [x] Failure of either child process is visible and causes the combined command to terminate or report failure.
- [x] The README or local development documentation explains environment variables, logs and shutdown.

## Out of scope

- Docker Compose orchestration, covered by #18.
- Unified unit/integration test command, covered by #20.

## Constraints

- Use the repository's existing frontend scripts and uv backend commands.
- Do not duplicate service configuration in application code.
- Keep the Makefile portable to the documented development environment.

## 12. [Done] Switch the frontend to the real backend
Goal: The frontend uses the running backend API instead of the mock service in normal development.
Description: Wire the existing typed HTTP service to the backend using the paths and payloads in `openapi.yaml`, including authentication/session behavior and actionable error states. Preserve a deliberate mock mode for isolated frontend development and tests, and update frontend unit tests for the real adapter's request and response behavior.

## Acceptance criteria

- [x] Normal API mode sends the frontend's supported reads and mutations to the backend base URL.
- [x] Request paths, methods, query parameters, JSON bodies and response parsing match `openapi.yaml`.
- [x] Authentication state is established, sent and cleared consistently for protected requests.
- [x] HTTP failures, validation errors and unauthorized responses produce visible actionable UI feedback.
- [x] Mock mode remains selectable for isolated frontend development and tests.
- [x] Frontend adapter tests cover representative success, empty, malformed and error responses.

## Out of scope

- Backend endpoint implementation, covered by #7–#9.
- Cross-service journey tests, covered by #13.
- Production deployment, covered by #18.

## Constraints

- Preserve the existing service interfaces and domain types.
- Do not silently fall back from API failures to mock data.
- Resolve the contract's bearer-token versus session-cookie behavior explicitly in the implementation.

## 13. [Done] Add frontend-backend integration tests
Goal: The frontend and in-memory backend work together over HTTP for the primary user journeys.
Description: Add integration coverage for loading jobs, viewing companies, authenticating, saving a job, submitting or withdrawing an application, and employer application updates. Run the frontend against the test backend without a database, seed deterministic fixtures, and verify both successful responses and user-visible failures.

## Acceptance criteria

- [x] Tests start a real backend and configure the frontend API adapter against it.
- [x] A public visitor can load jobs and company details through the frontend.
- [x] A candidate can authenticate, save a job, submit an application and see or withdraw it.
- [x] An employer can view a managed application and update its status.
- [x] At least one unauthorized, validation or duplicate flow is asserted through the visible UI.
- [x] Tests clean up server processes and pass repeatedly without a database.

## Out of scope

- Database-backed integration tests, covered by #15.
- Full Compose end-to-end testing, covered by #19.

## Constraints

- Use deterministic in-memory backend fixtures.
- Exercise the HTTP boundary rather than mocking the backend service.
- Follow the existing frontend test runner and uv commands.

## 14. [Done] Replace the in-memory store with SQLite and SQLAlchemy
Status: merged
Issue: https://github.com/Virgo-Alpha/steadwork/issues/14
Commits: `6151612`, `44d14e3`, `bdf59fd`, `796bada`, merge `8f932c3`
Goal: Persist the backend's current domain data in SQLite through SQLAlchemy while preserving the existing API contract and the in-memory store used by unit tests.
Description: Replace the production in-memory store with SQLAlchemy models and repositories backed by SQLite, preserving the existing API response and authorization behavior. Configure the database URL through an environment variable, keep database-specific details behind a persistence boundary, and retain an in-memory option for fast unit tests.

## Acceptance criteria

- [x] SQLAlchemy 2.x models and repositories persist users, companies, jobs, applications, candidate profiles, saved-job relationships, company memberships, and notifications; API operations read and mutate them through the persistence boundary.
- [x] A new SQLite database initializes with deterministic demo fixtures, preserves committed changes after backend restart, and does not overwrite existing records with seeds.
- [x] The backend reads the database URL from the environment, defaults to an ignored local SQLite file, accepts configured SQLite files, and fails clearly for invalid or unsupported URLs without falling back to memory.
- [x] Tests explicitly select the in-memory store and can reset isolated deterministic data without opening or modifying SQLite.
- [x] Implemented API routes preserve status codes, JSON fields, authentication, roles, ownership, validation errors, ordering, and password-hash confidentiality on SQLite.
- [x] SQLAlchemy relationships enforce valid references and safe delete rules for jobs, applications, users, profiles, saved jobs, memberships, and notifications.
- [x] Repository tests cover CRUD, relationships, duplicate and foreign-key constraints, database URL selection/failure, and isolation from the in-memory store.
- [x] Request-scoped sessions close after successful and failed requests; a later request succeeds with a fresh session after an error.
- [x] The in-memory unit suite passes, and the SQLite backend serves public, candidate, employer, and authentication flows.

## Out of scope

- HTTP integration tests against temporary SQLite databases and transactional cleanup, covered by [#15](https://github.com/Virgo-Alpha/steadwork/issues/15).
- Alembic schema migrations and upgrade tests, covered by [#16](https://github.com/Virgo-Alpha/steadwork/issues/16).
- PostgreSQL service and Docker Compose orchestration, covered by [#17](https://github.com/Virgo-Alpha/steadwork/issues/17).

## Constraints

- Keep persistence behind `backend/api/store.py`; route handlers do not query SQLAlchemy directly.
- Use SQLAlchemy 2.x ORM/repositories and uv; do not issue direct SQLite SQL.
- Preserve Django/DRF routes, `openapi.yaml`, bearer authentication, role/ownership behavior, and the in-memory test mode.
- Keep Alembic, PostgreSQL, Compose, credentials, and local database files out of this issue/repository changes.

## 15. [Done] Add database-backed integration tests
Status: merged
Issue: https://github.com/Virgo-Alpha/steadwork/issues/15
Commits: `0ec430e`, `bdf65d6`, merge `33c61bd`
Goal: Verify SQLite persistence and request behavior through the HTTP API using isolated temporary databases, while keeping the existing in-memory unit-test path independent.
Description: Add backend integration tests that exercise persistence, isolation, constraints, authentication, authorization, and lifecycle behavior through the API using temporary SQLite files. Preserve the current in-memory unit-test path and document a repeatable command for the SQLite integration suite.

## Acceptance criteria

- [x] Each SQLite integration test uses a new temporary SQLite database, configures the API to use it, and does not read or write the developer's default local database.
- [x] A test commits a change through one HTTP request and verifies it through a later request with a new request-scoped session.
- [x] Each test starts from deterministic fixtures; successful changes do not leak, failed requests leave no partial changes, and temporary databases, engines, and sessions are cleaned up.
- [x] Duplicate candidate or guest application requests return a client error and do not create a second application record.
- [x] Invalid foreign-key references are rejected and the database remains usable for a later request.
- [x] Job/application lifecycle and ownership rules are enforced through HTTP, including closed/expired job rejection and denial of another user's withdrawal or mutation.
- [x] Anonymous protected-route access and authenticated wrong-role/ownership access are rejected through HTTP.
- [x] The in-memory unit tests pass independently without creating, changing, or depending on a SQLite database.
- [x] Backend documentation gives the exact SQLite integration command and explains temporary database setup/cleanup; repeated runs leave no database files behind.

## Out of scope

- Alembic setup and migration/upgrade tests, covered by [#16](https://github.com/Virgo-Alpha/steadwork/issues/16).
- PostgreSQL compatibility, service configuration, and Compose workflows, covered by [#17](https://github.com/Virgo-Alpha/steadwork/issues/17).
- Browser and Compose end-to-end tests, covered by [#19](https://github.com/Virgo-Alpha/steadwork/issues/19).

## Constraints

- Keep tests in the backend suite and use DRF's HTTP test client; use the repository layer only for invalid foreign-key setup without a public endpoint.
- Use temporary SQLite databases and the SQLAlchemy persistence boundary from #14; never touch the developer's default local database.
- Preserve production API behavior, validation, authentication, and in-memory tests; do not weaken application rules to make tests pass.
- Do not add migrations, PostgreSQL, Compose, frontend/browser infrastructure, or production features.

## 16. [Done] Add database migrations
Status: merged
Issue: https://github.com/Virgo-Alpha/steadwork/issues/16
Commits: `a48d3d5`, `ab8eb73`, `22a543e`, merge `628f755`
Goal: A fresh environment can create and upgrade the schema without manually editing the database.
Description: Add a migration tool and an initial migration for all SQLAlchemy-backed entities used by the API. Document how to create, apply and inspect migrations, and test that a fresh SQLite database can be initialized and upgraded successfully.

## Acceptance criteria

- [x] Alembic is a backend dependency configured to use SQLAlchemy `Base.metadata` and the backend's `DATABASE_URL`.
- [x] The initial revision creates all eight current tables with the model's primary/unique/composite keys, indexes, nullability, foreign keys, and delete actions.
- [x] `uv run alembic upgrade head` initializes an empty temporary SQLite database, and `uv run alembic current` reports the expected head with all tables and constraints present.
- [x] Repeating `uv run alembic upgrade head` succeeds without duplicate objects or schema changes.
- [x] Migration commands use `DATABASE_URL` overrides or the default SQLite URL without touching the developer's database in tests.
- [x] Application startup does not use `Base.metadata.create_all()` as a migration substitute and reports a clear error for an unmigrated database.
- [x] Tests verify fresh upgrade, schema contents, repeated upgrade, current revision, and isolated database handling.
- [x] The backend README documents exact commands to create a revision, upgrade, inspect current revision, and run migration tests.
- [x] Existing SQLite and in-memory API behavior remains intact after migration integration.

## Out of scope

- PostgreSQL driver/service setup and applying migrations before Compose readiness, covered by [#17](https://github.com/Virgo-Alpha/steadwork/issues/17).
- Migration/schema changes for deferred product features, tracked by [#23](https://github.com/Virgo-Alpha/steadwork/issues/23).

## Constraints

- Keep Alembic configuration and committed migration revisions under `backend/`.
- Use Alembic with existing SQLAlchemy 2.x metadata and `uv`.
- Preserve database-agnostic models, API/auth behavior, and the in-memory test configuration.
- Do not add PostgreSQL, Docker Compose, future product tables, or ad hoc schema creation.

## 17. [Done] Run PostgreSQL with Docker Compose
Status: merged (review approved; QA PASS; post-merge regression passed)
Issue: https://github.com/Virgo-Alpha/steadwork/issues/17
Worktree: `/tmp/steadwork-issue-17` (`issue-17-postgres-compose`)
Engineer: `/root/engineer_17`
Commit: `850bc60` (`Run PostgreSQL backend with Docker Compose`)
Review worktree: `/tmp/steadwork-review-17` (`review-17-postgres-compose`; approved)
QA worktree: `/tmp/steadwork-qa-17` (`qa-17-postgres-compose`; PASS)
Merge commit: `4fcaae7` (`Merge issue #17 PostgreSQL Compose setup`)
Owned files: root Compose config, backend PostgreSQL/configuration integration and documentation, ignored env example as needed
Goal: A developer can start the backend and PostgreSQL together from the repository root, use persistent PostgreSQL-backed API data, and retain the existing SQLite development and test workflows.
Description: Provide a two-service Compose configuration for PostgreSQL and the existing Django/SQLAlchemy backend. Run Alembic migrations before the API accepts traffic, verify health and representative public/authenticated requests, and document persistent data lifecycle commands.

## Acceptance criteria

- [x] Root `docker-compose.yaml` declares exactly `postgres` and `app`, with no frontend or extra migration service.
- [x] PostgreSQL uses a named persistent volume and a health check; app waits for healthy postgres.
- [x] App receives `DATABASE_URL` pointing to the Compose PostgreSQL service; tracked files contain no usable database password.
- [x] App startup runs `uv run alembic upgrade head` before serving requests and fails if migration fails.
- [x] App readiness remains false until PostgreSQL-backed HTTP requests succeed; `/api/health/` returns 200 and reports `store: postgresql`.
- [x] Deterministic seed data loads on first API use for a fresh volume, is not duplicated on later requests/restarts, and does not overwrite existing data.
- [x] On a fresh stack, public `GET /api/jobs/` returns seeded jobs and unauthenticated `GET /api/auth/me/` returns 401.
- [x] Seeded candidate login returns a bearer token, and the token authenticates `GET /api/auth/me/`.
- [x] SQLite remains supported through `DATABASE_URL`, and both SQLite integration and existing test suites pass without PostgreSQL.
- [x] Backend docs provide copyable start, logs, stop-preserving-data, volume-reset, and shutdown commands and required environment variables.
- [x] Documentation identifies demo credentials as local only, not production secrets.

## Out of scope

- Multi-stage application image and frontend static-file serving, covered by [#18](https://github.com/Virgo-Alpha/steadwork/issues/18).
- CI service orchestration, covered by [#21](https://github.com/Virgo-Alpha/steadwork/issues/21).

## Constraints

- Keep Compose at repository root and use Alembic tooling from [#16](https://github.com/Virgo-Alpha/steadwork/issues/16).
- Keep application database access through SQLAlchemy and preserve `DATABASE_URL` configuration.
- Keep exactly `postgres` and `app`; run migrations as part of app startup, not a third service.
- Preserve SQLite local/test workflows and use non-secret local defaults or an ignored env file.
- Update backend docs with startup, logs, reset, and shutdown instructions.

## 18. Containerize the complete application
Status: merged (review approved; QA PASS; post-merge regression passed)
Issue: https://github.com/Virgo-Alpha/steadwork/issues/18
Worktree: `/tmp/steadwork-issue-18` (`issue-18-containerize`)
Engineer: `/root/engineer_18`
Owned files: root Dockerfile, docker-compose.yaml, backend static serving/configuration, container ignore/build behavior and relevant docs
Commits: `9975629` (initial implementation), `1fc7692` (cache fix), `97eb90e` (Compose check fix)
Review worktree: `/tmp/steadwork-review-18c` (`review-18-compose-check`; approved)
QA worktree: `/tmp/steadwork-qa-18` (`qa-18-containerize`; PASS)
Merge commit: `3c49692` (`Merge issue #18 complete application image`)
Goal: A developer can build and run the complete Steadwork application from the repository root with Docker Compose: the browser receives the frontend and its API requests reach the existing backend and PostgreSQL service.
Description: Add a root multi-stage Dockerfile that builds the Vite frontend and packages its static output with the Python backend. Update the existing two-service Compose configuration so the backend image serves both the frontend and `/api` from one application service.

## Acceptance criteria

- [x] The root `Dockerfile` has a Node frontend build stage that installs from `frontend/package-lock.json` and runs the frontend production build, followed by a Python backend runtime stage that installs from the committed uv lockfile.
- [x] The final application image contains the frontend build output and backend runtime; it does not include Node or frontend development dependencies at runtime.
- [x] With the stack running, `GET /` serves the frontend application and its built assets load successfully.
- [x] A client-side frontend route such as `/jobs` or a job detail URL serves the frontend entry point on direct navigation; paths under `/api/` continue to return backend responses and are never handled by the frontend fallback.
- [x] The frontend can use its existing same-origin `/api` requests through the application service; `GET /api/health/` reports the configured PostgreSQL store and a public API request succeeds.
- [x] Root `docker-compose.yaml` still declares exactly `postgres` and `app`; `app` builds from the root Dockerfile and Compose is the only application runtime service.
- [x] From a clean checkout with Docker and Compose, one documented root command builds and starts the complete stack without requiring host Node or Python installations.
- [x] PostgreSQL and application readiness checks remain active, and the application does not report healthy until the backend health endpoint succeeds.
- [x] Required configuration is passed through environment variables or the ignored local `.env` file, and `.env.example` documents the required names without credentials; no usable credentials, local databases, virtual environments, `node_modules`, or build/test artifacts enter the image.
- [x] Documentation provides copyable commands to build/start, inspect app and database logs, stop while preserving the named database volume, and remove the development volume.

## Out of scope

- Browser end-to-end coverage of user journeys, covered by [#19](https://github.com/Virgo-Alpha/steadwork/issues/19).
- Continuous integration workflow configuration, covered by [#21](https://github.com/Virgo-Alpha/steadwork/issues/21).
- The complete contributor README and project overview, covered by [#22](https://github.com/Virgo-Alpha/steadwork/issues/22).

## Constraints

- Reuse the PostgreSQL Compose setup from [#17](https://github.com/Virgo-Alpha/steadwork/issues/17), keeping exactly the `postgres` and `app` services.
- Keep frontend build and Python runtime in separate stages of the root Dockerfile; the final runtime uses the backend image only.
- Use the existing Vite output and lockfiles; keep API paths under `/api` and support frontend client-side route fallback without swallowing API or missing static asset requests.
- Do not require global Node or Python installations on the host.
- Do not add secrets, local databases, dependency caches, or test/build artifacts to the image.

## 19. Add full application-flow integration tests
Status: merged (review approved; QA PASS; post-merge E2E regression passed)
Issue: https://github.com/Virgo-Alpha/steadwork/issues/19
Worktree: `/tmp/steadwork-issue-19` (`issue-19-playwright-e2e`)
Engineer: `/root/engineer_19`
Owned files: repository-root `e2e/` tests/config/dependencies and test-only documentation if needed
Commit: `5725a26` (`Add Playwright job-board E2E harness`)
Review worktree: `/tmp/steadwork-review-19` (`review-19-playwright-e2e`; approved)
QA worktree: `/tmp/steadwork-qa-19` (`qa-19-playwright-e2e`; PASS)
Merge commit: `ae55858` (`Merge issue #19 Playwright E2E harness`)
Goal: Verify the supported job-board journey through the running application: a visitor discovers a seeded role, a candidate applies, and an employer reviews the application and changes its status.
Description: Add Playwright browser tests in the repository-root `e2e/` directory and run them against the app served by the two-service Compose stack.

## Acceptance criteria

- [x] Playwright browser tests live in the repository-root `e2e/` directory and run against the application served by the Compose stack from #18.
- [x] The harness starts an isolated Compose project with a fresh named database volume, waits for PostgreSQL and application health, and uses the app's browser-facing URL.
- [x] An unauthenticated visitor opens the frontend, sees a seeded published job, opens its details, and sees the application action.
- [x] A candidate signs in through the UI using seeded local demo credentials, submits an application to a seeded published internal job, and sees that application with status `Applied` in the candidate application view.
- [x] In a separate browser context, the seeded recruiter signs in, finds the submitted application in the employer flow, and changes its status to `Under Review`.
- [x] The candidate context observes `Under Review` in the candidate application view after refresh or navigation, demonstrating the update persisted through the application API.
- [x] An unauthorized candidate attempt to open employer application data is rejected and the frontend shows the access error without exposing the application list.
- [x] Browser contexts do not share authentication state; the visitor remains unauthenticated while candidate and recruiter actions occur in their own contexts.
- [x] The E2E assertions use browser-visible behavior and application HTTP responses; they do not query the database directly.
- [x] Harness cleanup removes the test Compose project and its named volume after success, assertion failure, startup failure, or interruption, without stopping or deleting another Compose project.

## Out of scope

- The requested interviewer/candidate session and shared-canvas journey is not supported by the current job-board app or product specifications; it is tracked for product/contract definition in [#24](https://github.com/Virgo-Alpha/steadwork/issues/24).
- A unified command that runs all suites, covered by [#20](https://github.com/Virgo-Alpha/steadwork/issues/20).
- CI workflow configuration, covered by [#21](https://github.com/Virgo-Alpha/steadwork/issues/21).

## Constraints

- Use the exact root `docker-compose.yaml` and application image from [#18](https://github.com/Virgo-Alpha/steadwork/issues/18); do not add a third Compose service.
- Use separate Playwright browser contexts for visitor, candidate and recruiter sessions.
- Read seeded local-only test account values from environment variables; do not embed credentials in test source or commit generated `.env` files.
- Exercise the frontend-facing application; do not bypass it with direct database assertions.
- Use an isolated Compose project name and test volume, and never remove a developer's normal database volume.
- Keep E2E test dependencies and configuration inside repository-root `e2e/`; the later unified-test task may invoke this harness.

## 20. Create one command for all unit and integration tests
Status: merged (review approved; QA PASS; post-merge regression passed)
Issue: https://github.com/Virgo-Alpha/steadwork/issues/20
Worktree: `/tmp/steadwork-issue-20` (`issue-20-unified-tests`)
Engineer: `/root/engineer_20`
Owned files: root Makefile and test-focused documentation/commands, preserving existing E2E harness and suite files
Commit: `1412758` (`Add unified test commands`)
Review worktree: `/tmp/steadwork-review-20` (`review-20-unified-tests`; approved)
QA worktree: `/tmp/steadwork-qa-20` (`qa-20-unified-tests`; PASS)
Merge commit: `2310ec5` (`Merge issue #20 unified test commands`)
Worktree: `/tmp/steadwork-issue-20` (`issue-20-unified-tests`)
Engineer: `/root/engineer_20`
Owned files: root Makefile and test-focused documentation/commands, preserving existing E2E harness and suite files
Goal: From the repository root, contributors can run the frontend, backend, frontend/backend integration, and Compose-backed browser test suites in a predictable order, or run the non-Compose checks in a fast mode.

## Acceptance criteria

- [x] `make test` runs the existing frontend Vitest suite, the existing backend pytest suite, and the root `e2e/` Playwright suite in that order; the frontend and backend suite commands include their existing unit and integration coverage.
- [x] Each stage prints a clear label, stops subsequent stages on failure, and returns a non-zero exit status identifying the failing stage.
- [x] `make test-fast` runs the frontend and backend suites with the same order and failure behavior, and does not start Docker Compose or run Playwright.
- [x] `make e2e` runs the existing isolated Compose-backed Playwright harness from `e2e/run.sh`; it does not duplicate E2E orchestration or query the database.
- [x] Test dependency setup is available through documented Make targets: frontend/backend dependencies use the existing npm and uv workflows, and E2E setup installs its locked Playwright dependency and required browser.
- [x] The test instructions document the root commands, required E2E demo-account environment variables, Docker/Compose requirement, and the harness's project/volume cleanup behavior.
- [x] Full `make test` includes `make e2e` by default; `make test-fast` is the explicit opt-out from Compose-backed E2E.

## Out of scope

- Adding or changing test cases, covered by [#19](https://github.com/Virgo-Alpha/steadwork/issues/19) and the existing frontend/backend suites.
- GitHub Actions scheduling, caching and workflow policy, covered by [#21](https://github.com/Virgo-Alpha/steadwork/issues/21).
- The complete project contributor guide and README rewrite, covered by [#22](https://github.com/Virgo-Alpha/steadwork/issues/22).

## Constraints

- Reuse the existing frontend npm, backend uv/pytest, and `e2e/` Playwright runner commands.
- Keep the existing `make dev`, `make install`, and setup behavior usable.
- Keep the full test stages deterministic and sequential; fail fast with a readable stage name.
- Do not duplicate Playwright Compose startup or cleanup logic already implemented in `e2e/run.sh`.
- Keep test documentation focused on test invocation; leave the full contributor README work for #22.

## 21. Set up continuous integration checks
Status: merged (review approved; QA PASS; post-merge full validation passed)
Issue: https://github.com/Virgo-Alpha/steadwork/issues/21
Worktree: `/tmp/steadwork-issue-21` (`issue-21-github-actions`)
Engineer: `/root/engineer_21`
Owned files: GitHub Actions workflow and CI-specific minimal docs/configuration only; no application/runtime/deployment changes
Commit: `4852507` (`ci: add GitHub Actions validation workflow`)
Review worktree: `/tmp/steadwork-review-21` (`review-21-github-actions`; approved)
QA worktree: `/tmp/steadwork-qa-21` (`qa-21-github-actions`; PASS)
Merge commit: `94c93e7` (`Merge issue #21 GitHub Actions workflow`)
Goal: Run the repository's unit, integration, and Compose-backed browser checks on pull requests and the default branch, with failures visible in GitHub Actions. Record a non-executing deployment plan for future work.

## Acceptance criteria

- [x] A GitHub Actions workflow runs for pull requests and pushes to the repository's default branch.
- [x] Frontend and backend test jobs run in parallel, install dependencies with npm and uv, and use the same Vitest and pytest suites as the local commands.
- [x] A full validation job runs the root `make test` command from [#20](https://github.com/Virgo-Alpha/steadwork/issues/20), including frontend/backend integration coverage and the Playwright E2E harness.
- [x] The E2E job builds and starts exactly the existing `postgres` and `app` services, waits for their health checks, and runs Playwright without querying the database directly.
- [x] The workflow runs the configured frontend typecheck/production build and a whitespace/diff check; it does not claim or require an unconfigured linter.
- [x] Any failed job or test stage returns a failed workflow with readable logs and its failing stage identified.
- [x] Dependency caches are keyed by the relevant lockfiles and do not include secrets, generated databases, or test Compose volumes.
- [x] A contributor can find the local equivalent commands and required E2E environment variables in the README or linked test instructions.
- [x] Any deployment plan in the workflow is inside comments only and cannot execute; it names AWS with GitHub OIDC as the preferred option, Render and Vercel as alternatives, and verifies future deployments through `/api/health/`.
- [x] The deployment comment also records Terraform where practical, one unified CI workflow before later dev/prod separation, and future OTel, Prometheus, Grafana, alerting, and an on-call engineer agent.

## Out of scope

- Actual production deployment and release publishing are tracked in [#25](https://github.com/Virgo-Alpha/steadwork/issues/25).
- New application test cases and the E2E harness are covered by [#19](https://github.com/Virgo-Alpha/steadwork/issues/19).
- The unified local test command is covered by [#20](https://github.com/Virgo-Alpha/steadwork/issues/20).
- The full contributor README rewrite is covered by [#22](https://github.com/Virgo-Alpha/steadwork/issues/22).

## Constraints

- Use GitHub Actions; do not add GitLab CI for this task.
- Pin or constrain action/runtime versions consistently.
- Keep credentials out of workflow files and logs; do not grant deployment permissions to pull-request jobs.
- Do not deploy, publish releases, or activate any commented deployment code.
- Keep observability and on-call automation as documented future work only.

## 22. Update the project README
Status: merged (review approved; QA PASS; post-merge documentation checks passed)
Issue: https://github.com/Virgo-Alpha/steadwork/issues/22
Worktree: `/tmp/steadwork-issue-22` (`issue-22-project-readme`)
Engineer: `/root/engineer_22`
Reviewer worktree: `/tmp/steadwork-review-22` (`issue-22-review`), commit `806f9e9`
QA worktree: `/tmp/steadwork-qa-22` (`issue-22-qa`)
Owned files: repository-root `README.md` only
Merged: `e2eb17c`
Goal: A new contributor can identify Steadwork’s intended users and current implementation, follow verified local setup and test instructions, and find the authoritative product, API, workflow, and backlog documents.

## Acceptance criteria

- [x] The README explains the tech job-board problem and identifies public visitors, candidates, recruiters/employers, and administrators as product roles.
- [x] It separates implemented behavior from the product target: current job discovery, company views, candidate and employer workflows, and authentication are described only to the extent supported by the frontend/backend; deferred or mock-only behavior is labeled accurately.
- [x] It states that the root product/API documents describe requirements or proposed contracts where they exceed the implemented API, and links to `openapi.yaml`, `_docs/specs.md`, `_docs/backend-plan.md`, and `_docs/job_board_project_scope.md`.
- [x] It documents the current architecture and runtime: React/Vite frontend; Django/DRF HTTP backend with SQLAlchemy/Alembic persistence; SQLite for local development and PostgreSQL through Compose; the default frontend API mode and opt-in mock mode.
- [x] It gives verified root-level setup and run commands (`make install` or `make setup`, `make dev`), the default local URLs, and how to stop services or locate their logs.
- [x] It gives verified test commands and explains their scope and prerequisites: `make test-setup`, `make test`, `make test-fast`, and `make e2e`, including the four E2E environment variable names, Docker/Compose requirement, and isolated E2E cleanup behavior. It does not publish account passwords or secrets.
- [x] It documents the actual Compose workflow and its two services (`postgres`, `app`), required `.env` variable names, startup/log/shutdown commands, persistence volume behavior, and the destructive effect of `docker compose down -v`; it links to `backend/README.md` for detailed database/migration instructions.
- [x] It describes the GitHub Actions triggers and checks, including that fork pull requests skip the secrets-dependent full E2E validation, and clearly says the workflow does not deploy or publish releases.
- [x] It has clear sections or equivalent navigation for frontend, backend, database/containerization, agent team, and task process, linking to `frontend/README.md`, `backend/README.md`, `_docs/team/pm.md`, `_docs/team/software-engineer.md`, `_docs/team/qa-engineer.md`, and `_docs/process.md`.
- [x] It links to `_docs/tasks.md` and the public repository issue tracker, and identifies #23 (deferred persistence requirements), #24 (collaborative-session product decision), and #25 (production deployment/release) as open follow-ups, not prerequisites for the README or completed capabilities.
- [x] All commands, local paths, URLs, environment variable names, links, and claims about current behavior are checked against the repository; no private-only resource, credential, or unsupported promise is included.

## Out of scope

- Implementing or expanding product/API behavior described in the product target; deferred persistence decisions are tracked in [#23](https://github.com/Virgo-Alpha/steadwork/issues/23), and collaborative interview/canvas scope is tracked in [#24](https://github.com/Virgo-Alpha/steadwork/issues/24).
- Production hosting, deployment, and release publishing, tracked in [#25](https://github.com/Virgo-Alpha/steadwork/issues/25).
- Changes to application code, CI behavior, or database/container implementation; those are outside this documentation task and are not prerequisites to it.

## Constraints

- Edit the root `README.md` only; link to existing repository documents rather than duplicating their detailed procedures.
- Treat the current application and workflow as the source of truth for implemented behavior; label aspirational or proposed requirements as such.
- Preserve the existing backend/API contract and avoid implying that incomplete endpoints, notifications, CV storage, team administration, moderation, or production deployment are live.
- Do not include credentials, secrets, or personal/private resource links.

## 23. Define persistence requirements for deferred product features
Status: ready
Issue: https://github.com/Virgo-Alpha/steadwork/issues/23
Goal: Specify persistence, lifecycle, authorization, and proposed API contracts for the confirmed deferred capabilities and create linked implementation issues only where the contract is sufficiently concrete.

## Acceptance criteria

- [ ] The requirements distinguish confirmed product scope from unresolved infrastructure and data-policy decisions. Confirmed scope includes company invitations/member administration, multiple CVs and per-application CV selection, external-apply click tracking without claiming submission completion, basic platform administration including suspension/removal, and asynchronous email with retries.
- [ ] For team management, define invitation and membership records/fields; company/user relationships; pending, accepted, revoked, and expired lifecycle behavior; admin/recruiter permissions; and create/list/resend/revoke/remove API operations. Specify that removed members lose company access.
- [ ] For CVs, define candidate-owned CV metadata and relationships to the candidate and applications, multiple/default/selected CV behavior, metadata lifecycle and APIs. Keep binary storage, access/download mechanics, validation limits, and retention tied to decision issue #26.
- [ ] For external applications, define the click event record, job and optional registered-candidate relationship, event creation/redirect API operation, guest behavior, duplicate/retry behavior, authorization, and explicitly state that a click does not prove application submission. Keep retention tied to #28.
- [ ] For moderation, define account suspension and job-removal records/state, actor/target relationships, affected-user access behavior, authorization, available admin operations, and required audit fields. Keep retention/audit policy tied to #28.
- [ ] For asynchronous email, define persisted message/outbox data, triggering domain events, recipient relationship, queued/attempting/sent/failed transitions, idempotency and API behavior on enqueue failure. Keep provider, queue/worker choice, retry/backoff and operations policy tied to #27.
- [ ] For every record, specify logical fields, relationships, deletion or retention behavior (or explicitly link unresolved policy to #26–#28), transitions, authorization, and the API operations that create/update it. Do not invent a retention duration.
- [ ] For each capability whose contract is implementable after applying decisions #26–#28, create a separate linked implementation issue. Each issue cites the approved specification section, schema/migration and API scope, authorization/lifecycle cases, tests, and dependencies; do not create an implementation ticket whose contract still depends on an unresolved decision.
- [ ] Update `_docs/specs.md` and `_docs/backend-plan.md` with the requirements, current-schema boundary, unresolved decisions, and links to all decision and implementation issues.
- [ ] The issue changes no application code, API implementation, database schema, migrations, dependencies, or runtime infrastructure.

## Out of scope

- Choosing CV file storage, access, and retention; tracked by [#26](https://github.com/Virgo-Alpha/steadwork/issues/26).
- Choosing email delivery, queue/worker, retry, and operations behavior; tracked by [#27](https://github.com/Virgo-Alpha/steadwork/issues/27).
- Setting retention and audit policy across deferred records; tracked by [#28](https://github.com/Virgo-Alpha/steadwork/issues/28).
- Implementing deferred APIs, persistence models, email delivery, CV storage, or moderation behavior.
- PostgreSQL and Compose, covered by [#17](https://github.com/Virgo-Alpha/steadwork/issues/17).

## Constraints

- Use `_docs/specs.md`, `_docs/backend-plan.md`, and confirmed decisions in `_docs/job_board_project_scope.md` as source requirements.
- Keep the currently implemented API and schema stable; treat the ORM and Alembic migrations as the authoritative current persistence boundary.
- Do not choose infrastructure for file or email storage or invent retention periods without an explicit product decision.
- Do not imply currently incomplete APIs, CV binary storage, email delivery, invitations, external click tracking, or moderation are implemented.

## 24. Define requirements for collaborative interview sessions and canvas
Status: backlog
Issue: https://github.com/Virgo-Alpha/steadwork/issues/24
Goal: Decide whether Steadwork should support interviewer and candidate interview sessions with a shared canvas, and define the product and technical contract before implementation.

## Acceptance criteria

- [ ] Product scope states whether collaborative interview sessions and a shared canvas belong in Steadwork.
- [ ] If in scope, requirements identify interviewer and candidate roles, session creation, invitation/join behavior, session ownership, and access after a link is shared.
- [ ] Requirements define session lifecycle, link expiry/revocation, authentication and authorization, and behavior when a participant disconnects or a session ends.
- [ ] Requirements define which canvas changes participants can make, how other participants observe them, and whether session/canvas state persists or is discarded.
- [ ] Privacy, data retention, cleanup, invalid/unauthorized actions, and relevant accessibility expectations are documented.
- [ ] The approved decisions and unresolved choices are recorded in the product/backend specifications; implementation work is split into issues with acceptance criteria and dependencies if the feature is approved.
- [ ] This task changes no application code, API implementation, database schema, or runtime infrastructure.

## Out of scope

- Implementing interview sessions or a shared canvas; that work will be specified and split into implementation issues here if approved.
- Job-board Playwright coverage, covered by [#19](https://github.com/Virgo-Alpha/steadwork/issues/19).

## Constraints

- Use existing product and backend specifications as source material.
- Do not assume a real-time transport, persistence policy, or security model before the product decisions are recorded.
- Keep the job-board MVP API and schema unchanged.

## 25. Plan and implement production deployment and release publishing
Status: backlog
Issue: https://github.com/Virgo-Alpha/steadwork/issues/25
Goal: Decide and implement a production deployment and release path for Steadwork after the CI workflow is stable.

## Acceptance criteria

- [ ] The approved hosting target and environment strategy (development/production) are recorded.
- [ ] Deployment credentials and permissions are documented and handled without committing secrets; AWS deployments use GitHub OIDC if selected.
- [ ] Infrastructure is defined in Terraform where practical, or the reason for another approach is documented.
- [ ] The workflow builds and publishes a release artifact and deploys only from an approved branch/tag and environment.
- [ ] Deployment verifies the service through `/api/health/` and reports health failure clearly.
- [ ] A rollback or recovery procedure is documented and verified for a failed deployment.
- [ ] The deployment can be exercised without publishing a release to production during pull-request checks.

## Out of scope

- The GitHub Actions CI workflow and non-executing deployment plan comment, covered by [#21](https://github.com/Virgo-Alpha/steadwork/issues/21).
- The full contributor and operations guide, covered by [#22](https://github.com/Virgo-Alpha/steadwork/issues/22).

## Constraints

- Use an explicitly selected hosting target; Render and Vercel remain alternatives to AWS until a decision is recorded.
- Keep production credentials out of the repository and workflow logs.
- Do not deploy from untrusted pull-request code.
- Add observability and on-call automation only through separately groomed work.

## 26. Decide CV file storage, access, and retention
Status: backlog
Issue: https://github.com/Virgo-Alpha/steadwork/issues/26
Goal: Choose the product and technical policy for storing and serving candidate CV files before defining their persistence/API implementation.

## Acceptance criteria

- [ ] Select storage for local development and production, including separation of files and credentials.
- [ ] Define accepted types, size limits, upload validation, and malware scanning policy.
- [ ] Define candidate and recruiter permissions for upload, list, download, select, and delete.
- [ ] Define authenticated download behavior and failed-upload cleanup.
- [ ] Define deletion/retention for candidate deletion, application retention, and backup expiry.
- [ ] Record the policy in `_docs/specs.md` and `_docs/backend-plan.md`, linked from #23.
- [ ] This issue changes no application code, API implementation, schema, or runtime infrastructure.

## Out of scope

- CV upload, file storage, metadata persistence, and download implementation; follow-up work depends on this decision and #23.

## Constraints

- Do not commit CV files, credentials, or personal data.
- Preserve multiple CVs and per-application CV selection.
- Make privacy, access, deletion, and backup behavior explicit before implementation.

## 27. Choose asynchronous email delivery and retry behavior
Status: backlog
Issue: https://github.com/Virgo-Alpha/steadwork/issues/27
Goal: Select the delivery and operational approach for the confirmed asynchronous email requirement.

## Acceptance criteria

- [ ] Select a provider/service boundary and background queue/worker approach with rationale.
- [ ] Define the message triggers for guest confirmations, application updates, recruiter alerts, verification, and password reset.
- [ ] Define retry/backoff, idempotency, terminal failure handling, operator visibility, and restart behavior.
- [ ] Define persisted message data, access restrictions, retention/deletion, and secret handling.
- [ ] Define a local/test path that does not send real email by default.
- [ ] Record the decision in `_docs/specs.md` and `_docs/backend-plan.md`, linked from #23.
- [ ] This issue changes no application code, API implementation, schema, runtime infrastructure, or secrets.

## Out of scope

- Email sending, queue persistence, workers, templates, and provider credentials; follow-up work depends on this decision and #23.

## Constraints

- Asynchronous delivery with retries is confirmed; Celery and Redis are options, not selected infrastructure.
- Do not commit API keys, credentials, or recipient data.

## 28. Set retention and audit policy for deferred records
Status: backlog
Issue: https://github.com/Virgo-Alpha/steadwork/issues/28
Goal: Decide retention for deferred records and personal data, and define which administrative actions need an audit trail.

## Acceptance criteria

- [ ] Define retention/deletion or anonymization for CV files and metadata, applications, external click events, invitations, notifications/email delivery records, and moderation actions.
- [ ] Define behavior on candidate/company deletion, member removal, job removal, invitation expiry, and terminal email failure.
- [ ] Define audited moderation/admin actions, actor/target/reason/time data, and audit access.
- [ ] Identify decisions needing product or legal review, responsible owner, and resolution path.
- [ ] Record approved rules in `_docs/specs.md` and `_docs/backend-plan.md`, linked from #23.
- [ ] This issue changes no application code, API implementation, schema, or runtime infrastructure.

## Out of scope

- Deletion jobs, anonymization, audit storage, and retention enforcement; these depend on the approved policy and #23.

## Constraints

- Do not invent retention periods or claim a legal requirement without an authoritative decision.
- Preserve existing MVP behavior until policy is recorded.
