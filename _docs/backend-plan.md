# Backend plan

The frontend currently uses `MockJobBoardService`; `VITE_DATA_MODE=api` selects the typed HTTP adapter. The endpoint map below is a proposed contract, not a live backend. Proposed API base is `/api`, with JSON resources:

- `GET /jobs/` (keyword, location, type, remote policy, experience, salary, skills, company, posted-within, sort), `GET /jobs/{id}/`, `GET /jobs/recommended/`
- `GET/POST /saved-jobs/`, `DELETE /saved-jobs/{jobId}/`
- `GET /companies/`, `GET /companies/{id}/`
- `GET/PATCH /candidate/profile/`, `GET /candidate/applications/`, `POST /applications/`, `POST /applications/guest/`, `POST /applications/{id}/withdraw/`
- `GET /employer/dashboard/`, `GET/POST /employer/jobs/`, `GET/PATCH /employer/jobs/{id}/`, `POST /employer/jobs/{id}/status/`
- `GET /employer/jobs/{id}/applications/`, `POST /employer/applications/{id}/status/`
- `GET /notifications/`, `POST /notifications/{id}/read/`; `GET /auth/me/`, `POST /auth/register/`, `POST /auth/login/`, `POST /auth/verify-email/`, `POST /auth/password-reset/`, and demo-only `POST /auth/demo-role/`

Assumptions: session-cookie authentication with CSRF protection for unsafe methods; public job/company reads and guest internal applications are allowed; candidate-only profile/save/withdraw permissions; company membership controls job and applicant access. CV uploads should use a separate multipart upload endpoint returning a stored file identifier; this initial mock uses named sample files. Company team invitations, admin moderation, verification, email delivery, and production auth are future backend work. Server-side validation, duplicate protection, lifecycle/deadline enforcement, and audit logging remain authoritative.

The confirmed backend architecture is Django REST Framework, with React on the
client. The implemented backend uses Django/DRF for HTTP routing, SQLAlchemy
for application records, and Alembic for migrations. SQLite is the persistent
local default; the root Compose stack configures PostgreSQL. The earlier
Express/Drizzle scaffold discrepancy was resolved in issue #5 by standardizing
on Django/DRF rather than introducing a second service. Keep this frontend
service contract stable.

## Deferred persistence requirements (proposed; not implemented)

Issue [#23](https://github.com/Virgo-Alpha/steadwork/issues/23) records the
proposed persistence and API contracts for confirmed future capabilities:
company invitations and membership administration, candidate CV metadata and
per-application selection, external apply click events, platform moderation,
and an asynchronous email outbox. It defines logical records, relationships,
lifecycle, authorization and operations in [_docs/specs.md](specs.md#14-deferred-persistence-and-api-contracts).
These are not part of the current API or schema. The current SQLAlchemy models
and Alembic revisions remain authoritative; no migrations or tables for these
features are implied.

The following decisions must be recorded before dependent implementation is
groomed:

- [#26](https://github.com/Virgo-Alpha/steadwork/issues/26) decides CV binary
  storage, authenticated access/download, validation and file-specific
  deletion/retention behavior.
- [#27](https://github.com/Virgo-Alpha/steadwork/issues/27) decides the email
  provider/service boundary, queue/worker, retry/backoff and operating policy.
- [#28](https://github.com/Virgo-Alpha/steadwork/issues/28) decides retention,
  deletion/anonymization and audit policy for deferred records and personal
  data. No retention period is selected in the current plan.

No feature implementation issue is ready yet because the proposed records
depend on #28, while CV implementation additionally depends on #26 and email
implementation additionally depends on #27. After the decisions are recorded,
#23 should be updated with separate implementation issues and their approved
schema, migration, API, authorization, lifecycle and test scope. Until then,
keep the existing schema and runtime unchanged; do not treat these proposed
records or operations as deployed behavior.
