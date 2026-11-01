# Steadwork backlog

## 1. [Done] Verify the frontend job discovery experience
Goal: Visitors can browse, search, filter, sort and view job details in the responsive frontend.
Description: Confirm the existing job list, search controls, filters, sorting, job detail page and company views against the requirements in `specs.md`. Keep the mock service as the data source and record this frontend slice as complete.
Status: Done

## 2. [Done] Verify candidate frontend workflows
Goal: Candidates can use the completed frontend flows for profiles, saved jobs, applications and notifications.
Description: Confirm the existing candidate-facing pages and states cover profile editing, saved jobs, application history, application submission, withdrawal and notification behavior described in `specs.md`. Keep these flows on the mock service until the real backend integration task.
Status: Done

## 3. [Done] Verify employer frontend workflows
Goal: Employers can use the completed frontend flows for job management and application review.
Description: Confirm the existing employer-facing pages and states cover dashboard metrics, job creation and management, job lifecycle changes, applicant lists and application status updates. Keep these flows on the mock service until the real backend integration task.
Status: Done

## 4. [Done] Verify responsive frontend behavior
Goal: The frontend remains usable on desktop, tablet and mobile viewport sizes.
Description: Check the completed responsive layout, navigation, forms, lists, detail pages and feedback states at the supported viewport sizes. Fix or document only frontend issues discovered during this verification; backend behavior remains out of scope.
Status: Done

## 5. Create the backend application skeleton
Goal: A runnable backend service exposes the `/api` base path and has a maintainable structure for implementing the OpenAPI contract.
Description: Choose and document the backend stack consistently with the project architecture decision, resolving the existing Express/Drizzle versus Django/DRF discrepancy before implementation. Create the application entry point, configuration, routers, models, store and test layout, and add a health or equivalent smoke endpoint without introducing a database dependency.

## 6. Implement the in-memory backend foundation
Goal: The backend serves seeded data from an in-memory store with modular routers, models, authentication and unit tests.
Description: Use an in-memory store and deterministic seed data so the frontend has useful jobs, companies, candidates and applications to display. Split the implementation into routers, models, store and auth modules; add hashed-password authentication and bearer-token authorization for protected endpoints; and write unit tests for the store, authentication and authorization behavior.

## 7. Implement the core public job and company API
Goal: Public frontend reads work against the backend for jobs and companies.
Description: Implement the public job list, job detail, company list and company detail endpoints from `openapi.yaml`, including the documented filters, sorting and error behavior. Keep the responses compatible with the existing TypeScript domain types and add unit tests for filtering, sorting, seeded data and missing resources.

## 8. Implement candidate and application API flows
Goal: Candidates and guests can complete the application flows defined by the API contract.
Description: Implement registration/login integration points as needed, candidate profile reads and updates, saved-job management, candidate application listing, registered applications, guest applications and withdrawals. Enforce authentication, candidate ownership, duplicate prevention and lifecycle validation, and add unit tests for successful and rejected cases.

## 9. Implement employer and notification API flows
Goal: Employers can manage jobs and applications, and users can read and update notifications.
Description: Implement employer dashboard, managed job CRUD/status operations, employer application listing/status updates, notification listing and notification read operations. Enforce company membership and role permissions, preserve the contract's response shapes, and add unit tests for ownership, permissions and status transitions.

## 10. Add backend API integration tests
Goal: The backend contract works through HTTP across its major public, candidate and employer flows.
Description: Add integration tests that start the backend with the seeded in-memory store and exercise representative requests through the HTTP layer. Cover authentication, public reads, candidate applications, employer operations, notifications, validation and protected-route failures, while keeping tests independent and repeatable.

## 11. Add a single-command local development Makefile
Goal: One command starts the frontend and backend together for local development.
Description: Create a Makefile with clear targets for installing or preparing dependencies, starting the frontend, starting the backend and starting both services concurrently. Document required environment variables, ports and how to stop the processes, and ensure the command works from a clean checkout without a database.

## 12. Switch the frontend to the real backend
Goal: The frontend uses the running backend API instead of the mock service in normal development.
Description: Wire the existing typed HTTP service to the backend using the paths and payloads in `openapi.yaml`, including authentication/session behavior and actionable error states. Preserve a deliberate mock mode for isolated frontend development and tests, and update frontend unit tests for the real adapter's request and response behavior.

## 13. Add frontend-backend integration tests
Goal: The frontend and in-memory backend work together over HTTP for the primary user journeys.
Description: Add integration coverage for loading jobs, viewing companies, authenticating, saving a job, submitting or withdrawing an application, and employer application updates. Run the frontend against the test backend without a database, seed deterministic fixtures, and verify both successful responses and user-visible failures.

## 14. Replace the in-memory store with SQLite and SQLAlchemy
Goal: The backend persists data in SQLite while keeping the API and store boundary database-agnostic.
Description: Replace the production in-memory store with SQLAlchemy models and repositories backed by SQLite, preserving the existing API response and authorization behavior. Configure the database URL through an environment variable, keep database-specific details behind a persistence boundary, and retain an in-memory option for fast unit tests.

## 15. Add database-backed integration tests
Goal: Persistence and backend behavior are verified against the SQLite implementation.
Description: Extend backend integration tests to run against a temporary SQLite database and verify data survives across requests, transactions roll back between tests, constraints prevent invalid or duplicate records, and authorization remains correct. Keep the existing in-memory unit-test path so tests remain fast and isolated.

## 16. Add database migrations
Goal: A fresh environment can create and upgrade the schema without manually editing the database.
Description: Add a migration tool and an initial migration for all SQLAlchemy-backed entities used by the API. Document how to create, apply and inspect migrations, and test that a fresh SQLite database can be initialized and upgraded successfully.

## 17. Run PostgreSQL with Docker Compose
Goal: Developers can run the backend against PostgreSQL locally using a documented Compose service.
Description: Add a PostgreSQL service and backend database configuration to Docker Compose, including non-secret development defaults supplied through environment variables. Verify the backend connects to PostgreSQL, migrations apply, seed data loads, and the API remains compatible with SQLite.

## 18. Containerize the complete application
Goal: The frontend, backend and database run together through Docker Compose with one command.
Description: Create production-appropriate frontend and backend container definitions and compose them with the database service, networking, health checks and required environment configuration. Provide a single startup command, verify the built frontend reaches the backend through the configured route, and document logs and shutdown behavior.

## 19. Add full application-flow integration tests
Goal: The containerized system passes an end-to-end test of the primary user journeys.
Description: Add tests that start the complete Compose stack and exercise public job discovery, authentication, candidate application tracking, employer review and status updates through the frontend-facing interface. Include startup readiness, seeded data, an authorization failure and cleanup so the suite is repeatable in local and CI environments.

## 20. Create one command for all unit and integration tests
Goal: A single documented command runs the complete test suite consistently.
Description: Add a project-level test command that runs frontend unit tests, backend unit tests, backend API integration tests and full application-flow integration tests in the supported order. Make failures return a non-zero exit code, expose useful output, and document any required services or environment variables.

## 21. Set up continuous integration checks
Goal: Every change is automatically checked before it is merged.
Description: Add CI configuration that installs frontend and backend dependencies, runs formatting or lint checks, executes the unified test command and starts required service dependencies for integration tests. Cache only safe dependencies, fail clearly on any check failure, and document the workflow's local equivalent.

## 22. Update the project README
Goal: A new contributor can understand the problem, system behavior, local setup and project status from the README.
Description: Rewrite or expand the README to explain the job-board problem, user roles, supported functionality, expected behavior, architecture, development commands and test commands. Include links to the relevant API/specification documents and a publicly accessible task tracker such as the repository's GitHub issues.
