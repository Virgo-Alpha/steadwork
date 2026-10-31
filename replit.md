# Steadwork Tech Job Board

A responsive technology hiring marketplace for candidates to discover and track roles and for companies to manage job postings and applicants. The current web build uses a mock service by default; no production API or authentication is connected yet.

## Run & Operate

- `pnpm --filter @workspace/api-server run dev` — run the API server (port 5000)
- `pnpm --filter @workspace/tech-job-board run test` — run the service-layer tests
- `pnpm --filter @workspace/tech-job-board run typecheck` — typecheck the web app
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- Required env: `DATABASE_URL` — Postgres connection string

## Stack

- pnpm workspaces, Node.js 24, TypeScript 5.9
- API: Express 5
- DB: PostgreSQL + Drizzle ORM
- Validation: Zod (`zod/v4`), `drizzle-zod`
- API codegen: Orval (from OpenAPI spec)
- Build: esbuild (CJS bundle)

## Where things live

- `artifacts/tech-job-board/src/App.tsx` — web routes and UI
- `artifacts/tech-job-board/src/domain/types.ts` — shared frontend service/domain types
- `artifacts/tech-job-board/src/services/` — service contract, mock implementation, and future HTTP adapter
- `artifacts/tech-job-board/backend-plan.md` — proposed REST endpoints and backend assumptions
- `attached_assets/job_board_project_scope_1793464487201.md` — confirmed product scope and decisions

## Architecture decisions

- All product data access goes through `JobBoardService`; pages must not call `fetch` or access browser storage directly.
- Mock mode is the default and persists demo records in browser storage. CV entries store filenames only; file bytes are not uploaded.
- `VITE_DATA_MODE=api` selects the HTTP adapter, but the proposed endpoints are not implemented yet.
- The supplied product scope selects Django REST Framework + PostgreSQL, while the current workspace API scaffold is Express + Drizzle. Resolve that runtime choice before implementing the real backend.

## Product

The first frontend covers public role search and recommendations, job details, guest and candidate applications, saved jobs, a candidate profile/CV-name library, application tracking, mock email/password auth screens, employer posting and applicant workflows, dashboard summaries, and in-app notifications.

## User preferences

No additional preferences recorded.

## Gotchas

- Mock sign-in, verification, reset, and role switching are demonstrations, not security controls or real email delivery.
- Real uploads need a storage-backed endpoint; do not treat mock CV filenames as uploaded files.
- Run the web app tests with `pnpm --filter @workspace/tech-job-board run test`.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
