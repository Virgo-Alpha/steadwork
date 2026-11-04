# Tech Job Board — Consolidated Specifications

Compiled from [Project scope and decisions](job_board_project_scope.md) and [Backend plan](backend-plan.md).

## 1. Purpose and status

Build a responsive tech job board where companies publish openings and manage applications, and job seekers discover, save, apply for and track jobs.

Product discovery is in progress, with decisions 1–25 confirmed. The API below is a proposed contract, not a live backend. Current mock behavior and deferred backend work do not replace the confirmed product requirements.

## 2. Required milestones

- Email/password authentication and role-based access.
- Job-seeker profiles containing relevant job-hunt information.
- Company job-posting management and per-job application counts.
- Candidate application tracking and saved jobs.
- Responsive desktop, tablet and mobile web experience.
- Bonus: job recommendations based on profile and posting skill tags.

## 3. Users, access and permissions

### Public visitors and guests

- Browse jobs and company profiles without signing in.
- Apply internally without creating an account by providing name, email, CV and an optional cover letter.
- Receive a guest application confirmation email, but cannot track application status.

### Registered candidates

- Manage their profile and CVs, save jobs, track applications and withdraw submitted applications.
- Candidate profile, save and withdrawal operations require candidate permissions.

### Companies and recruiters

- Companies have profiles and may invite multiple recruiters.
- Company registration is open: companies can publish jobs immediately without platform approval.
- Company admins manage company profiles, invitations and all company jobs.
- Recruiters create jobs and review applications.
- Company membership controls access to jobs and applicants.
- Team management includes email invitations, member lists, invitation resend/revocation and member removal.

### Platform administrators

- A basic admin dashboard manages users, companies, jobs and applications.
- Administrators can suspend accounts and remove inappropriate postings.

## 4. Authentication

- Support registration, login, email verification and password reset.
- Enforce role-based permissions; social login is outside MVP scope.
- The proposed API assumes session-cookie authentication with CSRF protection for unsafe methods.
- The demo role-switching endpoint is for demo use only.

## 5. Candidate profiles and CVs

- Use progressive profiles: begin with basic information and optionally add experience, education, preferences and other details later.
- Include skill tags for recommendations.
- Allow candidates to upload, manage and delete multiple CVs, set a default and select a CV for each application.
- CV uploads should use a separate multipart endpoint that returns a stored file identifier. Its route is not yet specified.
- The current mock uses named sample files instead of stored uploads.

## 6. Job postings and lifecycle

- Support draft, published, closed and expired jobs, with deadlines and reopening.
- Listings contain title, description, company, location, salary, job type, skills, experience, responsibilities, qualifications, benefits, remote policy, deadline and application method.
- Allow company-defined custom sections in addition to structured fields.
- Companies choose either an internal application form or an external application URL for each posting.
- Track external apply clicks separately; external submission completion cannot be reliably confirmed.
- Server-side lifecycle and deadline enforcement is authoritative.

## 7. Job discovery and recommendations

- Support keyword search and filters for location, job type, remote policy, salary, experience level, skills, company and posting date, plus sorting.
- Provide job listing and detail views, and public company listing and profile views.
- Recommend jobs using skill-tag overlap between candidate profiles and postings; AI/ML is not required.

## 8. Applications and candidate dashboard

### Internal applications

- Registered candidates apply using profile information, a selected or uploaded CV and an optional cover letter.
- Guest applications use the fields described in section 3.
- Recruiters update application statuses: Applied, Under Review, Shortlisted, Rejected and Hired.
- Registered candidates can see their application status.
- Prevent duplicate applications: one application per candidate per job. Guest email can help identify duplicates.
- Submitted applications cannot be edited.
- Registered candidates may withdraw at any time. Recruiters see the Withdrawn status, and candidates cannot reapply to the same job.
- Server-side validation and duplicate protection are authoritative.

### Candidate dashboard

- Show saved jobs and application history.
- Support filtering applications by status and date.
- Indicate saved-job availability.
- Track external applications separately from internal applications.

## 9. Employer dashboard and analytics

- Let companies track and manage their postings and review applicants for each job.
- Show active jobs, job counts, application counts, application statuses, recent applicants and trends over time.

## 10. Notifications and email

- Provide email and in-app notifications.
- Notify job seekers of application updates and recruiters of new applications.
- Provide an in-app notification center with read tracking.
- Send guest application confirmation emails.
- Queue email delivery asynchronously with retries. Celery and Redis are potential technologies; the choice is not finalized.

## 11. Client platform and architecture

- Deliver one responsive website for desktop, tablet and mobile. PWA and native mobile apps are outside MVP scope.
- The confirmed product architecture is React, Django REST Framework and PostgreSQL. The implemented backend is Django/DRF with SQLAlchemy and Alembic; local development uses SQLite and Compose configures PostgreSQL.
- The earlier Express/Drizzle scaffold discrepancy was resolved in issue #5; Django/DRF is the selected backend, not a second service.
- Keep the frontend service contract stable as the backend evolves.
- The frontend uses the typed HTTP adapter by default; `VITE_DATA_MODE=mock` opts into the browser-storage mock service.

## 12. Proposed API contract

The proposed base path is `/api`; resources use JSON, with a separate multipart upload endpoint for CV files. Paths below are relative to the base path.

| Area | Method and path | Purpose |
|---|---|---|
| Jobs | `GET /jobs/` | Search, filter and sort jobs by keyword, location, type, remote policy, experience, salary, skills, company and posted-within. |
| Jobs | `GET /jobs/{id}/` | Read a job. |
| Jobs | `GET /jobs/recommended/` | Get recommended jobs. |
| Saved jobs | `GET /saved-jobs/` | List saved jobs. |
| Saved jobs | `POST /saved-jobs/` | Save a job. |
| Saved jobs | `DELETE /saved-jobs/{jobId}/` | Remove a saved job. |
| Companies | `GET /companies/` | List companies. |
| Companies | `GET /companies/{id}/` | Read a company profile. |
| Candidate | `GET /candidate/profile/` | Read the candidate profile. |
| Candidate | `PATCH /candidate/profile/` | Update the candidate profile. |
| Candidate | `GET /candidate/applications/` | List candidate applications. |
| Applications | `POST /applications/` | Submit a registered candidate application. |
| Applications | `POST /applications/guest/` | Submit a guest application. |
| Applications | `POST /applications/{id}/withdraw/` | Withdraw a registered candidate application. |
| Employer | `GET /employer/dashboard/` | Read recruitment dashboard data. |
| Employer | `GET /employer/jobs/` | List company jobs. |
| Employer | `POST /employer/jobs/` | Create a job. |
| Employer | `GET /employer/jobs/{id}/` | Read a managed job. |
| Employer | `PATCH /employer/jobs/{id}/` | Update a managed job. |
| Employer | `POST /employer/jobs/{id}/status/` | Change a job's lifecycle status. |
| Employer | `GET /employer/jobs/{id}/applications/` | List applications for a job. |
| Employer | `POST /employer/applications/{id}/status/` | Change an application status. |
| Notifications | `GET /notifications/` | List notifications. |
| Notifications | `POST /notifications/{id}/read/` | Mark a notification as read. |
| Authentication | `GET /auth/me/` | Read the current authenticated user. |
| Authentication | `POST /auth/register/` | Register an account. |
| Authentication | `POST /auth/login/` | Log in. |
| Authentication | `POST /auth/verify-email/` | Verify an email address. |
| Authentication | `POST /auth/password-reset/` | Support password reset. |
| Demo only | `POST /auth/demo-role/` | Switch demo roles. |

## 13. Backend completion and unresolved details

- Registration, login, email verification, password reset, candidate recommendations, and current candidate/employer endpoints are implemented. Verification and reset mail use the configured Django email backend; hosted environments must configure SMTP. Company team invitations and admin moderation remain future backend work.
- Company registration now has an API contract and creates the company plus its initial recruiter membership. Company profile editing, team management, file-backed CV uploads, moderation, and external-click routes remain deferred; Section 14 records proposed contracts, with decisions #26–#28 still pending where noted.
- Request/response schemas, detailed validation rules and error formats are not supplied by the source documents.
- Configure SMTP for hosted email and decide whether email delivery needs an asynchronous worker at production scale.
- Enforce validation, duplicate protection, permissions, lifecycle/deadline rules and audit logging on the server.

## 14. Deferred persistence and API contracts

This section specifies proposed future records and operations for confirmed product requirements. It is a contract for later implementation, not a description of tables, routes, or behavior currently present in the backend or frontend API. The current boundary is the SQLAlchemy mappings and Alembic migrations: `users`, `companies`, `jobs`, `applications`, `candidate_profiles`, `saved_jobs`, `company_memberships`, and `notifications`. In particular, `ApplicationRecord.cv_name` is text metadata; it is not a stored CV or a file reference. No records or migrations below are implemented.

### Company invitations and membership administration

The existing `company_memberships` record associates a user and company with a role. Future team management needs a separate invitation record and an explicit active-membership lifecycle:

| Proposed record | Logical fields and relationships | Lifecycle and access |
|---|---|---|
| `CompanyInvitation` | Opaque ID; company ID; normalized invitee email; invited role (`admin` or `recruiter`); inviter user ID; token digest; created, expiry, accepted, revoked and last-sent timestamps; state. References `companies`, the inviter in `users`, and optionally the accepting user. | `pending → accepted`, `pending → revoked`, or `pending → expired`. Acceptance creates an active membership for the accepting account; resend keeps the invitation pending, rotates its secret, and records a send time. An active pending invitation for the same company/email is unique. Expired and revoked invitations cannot be accepted. |
| `CompanyMembership` (existing record extended by lifecycle metadata if needed) | User ID, company ID, role, and created/removed timestamps and actor when removal history is retained. Unique active user/company pair. | `active → removed`; removal immediately revokes company access. Company admins manage invitations, members and company jobs; recruiters manage jobs and review applicants. Historical removal data is subject to #28. |

Proposed operations are `GET/POST /companies/{companyId}/invitations/`, `POST /companies/{companyId}/invitations/{invitationId}/resend/`, `POST /companies/{companyId}/invitations/{invitationId}/revoke/`, `POST /company-invitations/{token}/accept/`, `GET /companies/{companyId}/members/`, and `DELETE /companies/{companyId}/members/{userId}/`. Invite creation, resend, revoke and member removal require a company admin; acceptance requires a valid invitation and an authenticated account whose email matches the invitation; listing is limited to company members and their role. Invitation secrets are opaque and single-use; only their digest is stored. These proposed routes are not in the current API contract.

Whether expired/revoked invitations and removed-membership history are retained, anonymized or deleted, including what happens when a company or user is deleted, is unresolved under [#28](https://github.com/Virgo-Alpha/steadwork/issues/28). Do not assume that cascading deletion of the current membership row is sufficient to meet future audit and retention requirements.

### CV metadata and per-application selection

The candidate owns zero or more CV metadata records. A proposed `CandidateCv` has an opaque ID, candidate user ID, display name, original filename, media type, byte size, opaque storage reference, default flag, lifecycle state, and created/updated/deleted timestamps. The storage reference is only a logical indirection; its format and storage system are undecided. A candidate may have multiple active CVs and at most one default. Setting a default clears the previous default atomically. Application submission records the selected CV ID plus a display-name snapshot so an application can identify the selection made at submission; no file is embedded in an application record. The lifecycle is `upload-pending → available` or `upload-pending → failed`; an available CV can transition to `deletion-pending → deleted` or be retained in a restricted, non-selectable state if #26/#28 require preserving an application reference. A CV cannot be selected after deletion or while its upload is incomplete or failed. Failed-upload cleanup is defined by #26.

Proposed operations are `GET/POST /candidate/cvs/`, `GET/PATCH/DELETE /candidate/cvs/{cvId}/`, `POST /candidate/cvs/{cvId}/default/`, and a multipart upload operation whose exact route and download mechanism remain under decision #26. Candidates may list, upload, rename, select, and delete only their own CVs. A recruiter may access the selected CV only through an application for a job in a company they can manage; this is subject to #26's access/download decision. The lifecycle includes upload-pending, available, failed, and deletion-pending states. Binary storage, access/download mechanics, validation and size limits, malware scanning, and file deletion/retention rules are explicitly unresolved in [#26](https://github.com/Virgo-Alpha/steadwork/issues/26); data retention and the fate of application references are also subject to [#28](https://github.com/Virgo-Alpha/steadwork/issues/28). No file size, content type, retention duration, or storage technology is selected here.

### External application click tracking

An external click is an event, not an application. A proposed `ExternalApplyClick` record contains an opaque ID, job ID, nullable registered candidate user ID, click timestamp, and an idempotency key. It has no candidate email, CV, or claimed external submission status. A unique idempotency key scopes retries of one intentional click; separate intentional clicks create separate events. Guest clicks have a null candidate ID. Click rows refer to a job and optionally a user and do not prevent either record from following its existing lifecycle.

The proposed public operation `POST /jobs/{jobId}/external-clicks/` requires an `Idempotency-Key` unique to one intentional click. It verifies the job is published, open, and configured for an external URL, records one event for the `(jobId, idempotencyKey)` pair, then redirects to the configured URL. Repeating the same key returns the same redirect without adding a count; a later intentional click uses a new key. The backend derives an optional candidate ID from the authenticated session rather than trusting a body-supplied user ID. It rejects internal-application jobs and invalid/closed jobs. `GET /employer/jobs/{jobId}/external-clicks/summary/` returns aggregate counts only to authorized company members; raw event data is restricted to platform administrators. A click never proves that a visitor completed an external application. Deletion and retention are unresolved under [#28](https://github.com/Virgo-Alpha/steadwork/issues/28). Neither operation is currently implemented.

### Platform moderation and suspension

Moderation must preserve a record of administrative action rather than overloading ordinary employer job status. A proposed append-only `ModerationAction` records an ID, action (`suspend_account`, `lift_suspension`, `remove_job`, or `restore_job`), admin actor ID, target type and ID, reason, and action timestamp. It references the actor in `users`; the target is an existing user or job. The current state is derived from the latest unreversed action for that target, or may be represented by an explicit suspension/removal state linked to its originating action. Administrative actions record their reversal as another action; records are not silently edited to erase the decision. Audit-field access and retention are governed by #28.

Only platform administrators can list users, companies, jobs and applications in the proposed `/admin/` resource family, suspend or reinstate accounts, and remove or restore job postings. Proposed operations include `GET /admin/users/`, `GET /admin/companies/`, `GET /admin/jobs/`, `GET /admin/applications/`, `POST /admin/users/{userId}/suspension/`, `POST /admin/users/{userId}/suspension/lift/`, `POST /admin/jobs/{jobId}/removal/`, and `POST /admin/jobs/{jobId}/restoration/`. Each action requires a reason and creates an audit record. A suspended user cannot authenticate or use protected operations. A removed job is excluded from public reads and new applications while existing application records remain unchanged. Admins can still inspect affected records. Audit access, reason detail and retention are unresolved under [#28](https://github.com/Virgo-Alpha/steadwork/issues/28). These routes and effects are not currently implemented.

### Asynchronous email outbox

The confirmed requirement is to enqueue email asynchronously and retry transient delivery failures. A proposed `EmailOutboxMessage` has an opaque ID, message type, recipient user ID when applicable, recipient address snapshot for delivery, minimal template/context data, unique idempotency key, state, attempt count, created/updated/next-attempt/sent/terminal-failure timestamps, and a last failure category safe for operator diagnostics. It references a user when a recipient account exists; guest application messages have no user relationship. A domain event and outbox row are committed atomically so a successful domain operation cannot lose its notification between database commit and queue publication.

Message types cover guest application confirmation, candidate application status, recruiter new-application alert, email verification, and password reset. The proposed state progression is `queued → attempting → sent`, with transient failures returning to `queued` for retry and exhausted/permanent failures becoming `failed`; a worker lease/claim prevents simultaneous delivery of one row. Use provider-supported idempotency keys when available. If the provider cannot deduplicate a retry after an uncertain outcome, delivery is at least once and a duplicate email is possible; a message key supports reconciliation but does not prevent that duplicate. Only the backend worker may claim or update delivery state; an authorized operator may request retry/replay through a restricted administrative operation, which creates an auditable action rather than directly editing message state. The provider choice and exact operator permissions remain for #27 to finalize.

No public email-sending API is exposed. Existing domain operations enqueue the relevant message; a worker claims and delivers outbox rows. If the outbox row cannot be durably committed, the triggering API operation returns a retryable `503 Service Unavailable` and its domain transaction is rolled back. Once enqueueing commits, provider failure is handled asynchronously and does not undo the domain operation. Provider, queue/worker technology, backoff schedule, retry limit, operator tooling, and operational failure policy remain unresolved in [#27](https://github.com/Virgo-Alpha/steadwork/issues/27). Recipient and payload retention/deletion remains governed by [#28](https://github.com/Virgo-Alpha/steadwork/issues/28). Do not persist credentials in message rows or logs. Email and outbox persistence/delivery are not currently implemented.

### Implementation issue readiness

No persistence implementation issue is ready to create yet. Company invitation history, CV storage/access and application references, external-click data, moderation audit records, and email payloads all need the retention/deletion policy in #28; CV files additionally depend on #26, and outbox/provider behavior depends on #27. Revisit implementation issue creation after #26–#28 are resolved. Until then, these contracts remain proposed, the existing ORM/migrations remain authoritative, and no new table is implied.
