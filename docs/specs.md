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
- The confirmed architecture is React, Django REST Framework and PostgreSQL.
- The backend plan reports that the current workspace API scaffold uses Express 5 with Drizzle. Implementation must resolve whether Django runs as a separate service or the selected backend stack changes.
- Keep the frontend service contract stable through that decision.
- The frontend currently uses `MockJobBoardService`; `VITE_DATA_MODE=api` selects the typed HTTP adapter.

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

- Production authentication, verification, company team invitations, admin moderation and email delivery remain future backend work in the backend plan, while remaining confirmed product requirements.
- The endpoint map does not yet specify all operations needed for company registration/profile management, team management, CV management, platform administration or external apply-click tracking. Those contracts still need definition.
- Request/response schemas, detailed validation rules and error formats are not supplied by the source documents.
- Resolve the Django versus Express scaffold decision and finalize the asynchronous email technology.
- Enforce validation, duplicate protection, permissions, lifecycle/deadline rules and audit logging on the server.
