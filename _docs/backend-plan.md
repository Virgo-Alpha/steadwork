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

The confirmed backend architecture is Django REST Framework, with PostgreSQL
planned for the persistence milestone. The earlier workspace API scaffold
referenced Express 5 with Drizzle; issue 5 resolves that discrepancy by
standardizing the backend on Django/DRF rather than introducing a second
service. The issue-5 skeleton therefore uses Django URL routing and DRF views,
with a dependency-free dummy database configuration until the persistence
milestone adds PostgreSQL. Keep this frontend service contract stable.
