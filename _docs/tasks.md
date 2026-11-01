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
Goal: A single multi-stage image serves the frontend and backend through the two-service Docker Compose stack.
Description: Create one root `Dockerfile` with a Node build stage for the frontend followed by a Python runtime stage for the backend. Copy the built frontend static files into the backend image, configure the backend to serve them, and use `docker-compose.yaml` with only `postgres` and `app`.

## Acceptance criteria

- [ ] The root `Dockerfile` has a frontend Node build stage and a Python backend runtime stage.
- [ ] The frontend build output is copied into the Python backend image.
- [ ] The backend serves the frontend static files and routes API requests under `/api`.
- [ ] `docker-compose.yaml` contains only `postgres` and `app`, and one documented command builds and starts both.
- [ ] Backend and database readiness checks gate dependent startup.
- [ ] Required configuration is supplied through environment variables with safe documented defaults.
- [ ] A clean host can inspect logs, stop the stack and remove development data with documented commands.
- [ ] Container builds do not include secrets, local databases or unnecessary development artifacts.

## Out of scope

- Full end-to-end flow tests, covered by #19.
- CI workflow configuration, covered by #21.

## Constraints

- Reuse the two-service PostgreSQL Compose setup from #17.
- Keep frontend build and backend runtime concerns in separate Dockerfile stages, not separate Compose services.
- Do not require global runtime installations beyond Docker/Compose.
- Use the backend image as the only application image.

## 19. Add full application-flow integration tests
Goal: Playwright verifies both complete application flows against `docker-compose.yaml`.
Description: Put Playwright tests in the repository-root `e2e/` directory and run them against the two-service Compose stack. Cover the existing job-board journey and the requested two-session interviewer/candidate canvas journey, including shared-session visibility and cleanup.

## Acceptance criteria

- [ ] Playwright tests live in the repository-root `e2e/` directory.
- [ ] The test harness starts `docker-compose.yaml` and waits for `postgres` and `app` readiness.
- [ ] A visitor can discover a seeded job through the frontend-facing interface.
- [ ] A candidate can authenticate, apply, view the application and receive an updated status.
- [ ] An employer can review that application and change its status.
- [ ] Session 1 logs in as the interviewer and creates an interview session.
- [ ] Session 1 shares a join link, and session 2 joins as the candidate.
- [ ] Session 2 changes the canvas, and session 1 visibly observes the change.
- [ ] At least one unauthorized or invalid action is verified as rejected and visible.
- [ ] The harness always cleans up containers and volumes after success or failure.

## Out of scope

- Writing the unified local test command, covered by #20.
- CI-specific caching and workflow policy, covered by #21.

## Constraints

- Use the exact `docker-compose.yaml` and application image from #18.
- Do not bypass the frontend/backend boundary with direct database assertions.
- Use isolated test data and avoid committed credentials.
- Use Playwright browser contexts or equivalent separate clients for sessions 1 and 2.

## 20. Create one command for all unit and integration tests
Goal: A single documented command runs all checks, with `make e2e` dedicated to Compose-backed Playwright tests.
Description: Add project-level Make targets that run frontend unit tests, backend unit tests, backend API integration tests, frontend/backend integration tests and the root `e2e/` suite. `make e2e` must start or use `docker-compose.yaml`, run Playwright, and clean up; the unified command must invoke it after the prerequisite checks.

## Acceptance criteria

- [ ] One documented command runs frontend unit, backend unit, backend API integration, frontend/backend integration and full Playwright E2E tests.
- [ ] `make e2e` runs the root `e2e/` Playwright suite against `docker-compose.yaml`.
- [ ] The command runs prerequisite setup in a deterministic order.
- [ ] Any failed suite returns a non-zero exit code and identifies the failing stage.
- [ ] The command documents required environment variables, Docker/Compose services and cleanup.
- [ ] The full command runs `make e2e` by default, while an explicit fast mode omits Compose E2E tests.

## Out of scope

- Adding new test cases, covered by #10, #13, #15 and #19.
- CI workflow scheduling and permissions, covered by #21.

## Constraints

- Reuse existing test runners and Makefile/Compose targets.
- Do not duplicate test logic in shell scripts.
- Keep local and CI invocation names consistent.
- Keep the E2E test command independent from direct database access.

## 21. Set up continuous integration checks
Goal: GitHub Actions automatically runs parallel checks, Compose-backed integration/E2E tests, and a documented future deployment path.
Description: Add a GitHub Actions CI/CD workflow that runs frontend and backend tests in parallel, builds the two-service Docker Compose stack, runs integration tests and `make e2e` against it, and fails clearly on errors. Include deployment only as a commented block: document AWS deployment with a GitHub OIDC role, note Render and Vercel as alternatives, and include the requested future validation and operations notes without implementing deployment.

## Acceptance criteria

- [ ] Pull requests and the default branch trigger a GitHub Actions workflow.
- [ ] CI installs frontend and backend dependencies using the repository-standard tools.
- [ ] Frontend and backend unit/test jobs run in parallel.
- [ ] CI builds the two-service Docker Compose stack and waits for readiness.
- [ ] CI runs integration tests and `make e2e` against that Compose stack.
- [ ] CI runs formatting/lint checks and the unified test command from #20.
- [ ] Any failed check fails the workflow with readable logs.
- [ ] Dependency caching is scoped safely and does not cache secrets or generated databases.
- [ ] The README documents the local equivalent of the CI checks.
- [ ] The deployment step is commented out and not executable; its comment specifies AWS with a GitHub OIDC role, considers Render and Vercel, and says deployment success should later be checked through the health endpoint.
- [ ] The deployment comment says to use Terraform where possible, start with one unified CI workflow and later separate dev/prod branches, and add future OTel, Prometheus, Grafana, alerting and an on-call engineer agent.

## Out of scope

- New application behavior or tests, covered by #19 and #20.
- Production deployment and release publishing.

## Constraints

- Use GitHub Actions; do not add GitLab CI for this task.
- Pin or constrain action/runtime versions consistently.
- Keep credentials out of workflow files and logs.
- Do not implement or trigger deployment in this task.
- Keep observability and on-call automation as documented future work only.

## 22. Update the project README
Goal: A new contributor can understand the problem, system behavior, local setup and project status from the README.
Description: Rewrite or expand the README into a complete contributor guide. Explain the problem and expected behavior, then cover the frontend, backend, agent team, process, database, containerization, setup, Make commands, GitHub Actions and the public task tracker.

## Acceptance criteria

- [ ] The README explains the job-board problem and intended users.
- [ ] It describes supported public, candidate, employer and authentication behavior, including important limitations.
- [ ] It documents the architecture, configuration, local development and test commands.
- [ ] It has explicit sections for frontend, backend, agent team, process, database and containerization.
- [ ] It documents setup and running with Make, including `make dev`, the unified test command and `make e2e`.
- [ ] It explains GitHub Actions checks and the fact that deployment is not enabled yet.
- [ ] It links to `openapi.yaml`, the relevant `_docs` specifications and the public GitHub issue tracker.
- [ ] It explains mock, SQLite and PostgreSQL modes and the expected Docker Compose workflow.
- [ ] Commands and links are checked against the repository and do not point to private-only resources.

## Out of scope

- Implementing functionality described in the README, covered by #5–#21.
- Product requirements changes beyond the existing specifications.

## Constraints

- Keep documentation accurate to the implemented behavior.
- Use repository-relative links for local documents.
- Do not include secrets, personal credentials or unsupported promises.

## 23. Define persistence requirements for deferred product features
Status: backlog
Issue: https://github.com/Virgo-Alpha/steadwork/issues/23
Goal: Define persisted data, relationships, lifecycle rules, and API contracts for confirmed product capabilities outside the current API.
Description: Inventory deferred team management, CV metadata/lifecycle, external apply tracking, platform moderation, and email delivery requirements. Resolve or explicitly track decisions and split approved persistence work into implementation issues without changing the current schema in this task.

## Acceptance criteria

- [ ] The inventory covers team invitations/member administration, CV metadata/lifecycle, external application click tracking, platform moderation/suspension, and asynchronous email delivery where each remains in scope.
- [ ] For each selected capability, requirements identify records/fields, relationships/deletion/retention, state transitions, authorization, and API operations.
- [ ] Unresolved choices such as CV binary storage and email delivery/retry infrastructure are documented or assigned decision issues.
- [ ] Approved capabilities needing tables are split into implementation issues with acceptance criteria and dependencies; this task adds no unsupported tables.
- [ ] Product/backend specifications link to the decisions and implementation issues.

## Out of scope

- Implementing deferred APIs, persistence models, email delivery, CV storage, or moderation behavior.
- PostgreSQL and Compose, covered by [#17](https://github.com/Virgo-Alpha/steadwork/issues/17).

## Constraints

- Use `_docs/specs.md` and `_docs/backend-plan.md` as source requirements.
- Keep the current API and schema stable until feature contracts are agreed.
- Do not choose file or email storage infrastructure without a product decision.
