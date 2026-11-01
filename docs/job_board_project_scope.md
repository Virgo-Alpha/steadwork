# Tech Job Board — Project Scope and Decisions

**Status:** Discovery in progress. Decisions 1–25 confirmed.

## Assignment

Develop a job board where companies can post tech job openings and users can search and apply for positions. Implement authentication and responsive design.

### Required milestones
- User authentication.
- Job-seeker profiles containing relevant job-hunt information.
- Companies can track their job postings.
- Companies can view application counts for each job.
- Job seekers can track applications and save jobs for later.
- Responsive application.
- Bonus: recommend jobs based on skill tags on profiles and postings.

## Confirmed product decisions

| # | Area | Selected option | Scope |
|---|---|---|---|
| 1 | Company accounts | B — Company accounts | Companies have profiles and can invite multiple recruiters to manage jobs. |
| 2 | Application methods | C — Hybrid | Companies choose internal applications or an external application URL. External apply clicks can be tracked, but submission completion cannot be reliably confirmed. |
| 3 | Job-seeker profiles | D — Progressive | Start with basic information; optionally add experience, education, preferences and other details later. |
| 4 | Application management | B — Status tracking | Recruiters update statuses (Applied, Under Review, Shortlisted, Rejected, Hired); registered candidates see their status. External applications are tracked separately. |
| 5 | Job posting lifecycle | B — Lifecycle management | Draft, published, closed and expired jobs; deadlines and reopening. |
| 6 | Job discovery | B — Advanced search | Keyword search; filter by location, job type, remote work, salary, experience level, skills, company and posting date; sorting. |
| 7 | Authentication | A — Email/password | Registration, login, email verification, password reset, and role-based permissions. No social login in MVP. |
| 8 | Company permissions | B — Admin/recruiter | Company admins manage profiles, invitations and all jobs; recruiters create jobs and review applications. |
| 9 | Notifications | C — Email + in-app | Job seekers receive application updates; recruiters receive new-application alerts; in-app notification center. |
| 10 | Candidate dashboard | B — Organized dashboard | Saved jobs, application history, filters by status/date, and saved-job availability. |
| 11 | Internal application form | B — Standard | Profile information, choice/upload of CV, optional cover letter. |
| 12 | Company onboarding | A — Open registration | Anyone can register a company and immediately publish jobs without platform approval. |
| 13 | Public access | C — Guest applications | Public browsing and company profiles; guests can apply without an account. Registered users can save jobs and track applications. |
| 14 | Guest application workflow | A — Simple | Guest supplies name, email, CV and optional cover letter; receives confirmation email but cannot track status. |
| 15 | Employer analytics | B — Recruitment dashboard | Active jobs, job counts, application counts, statuses, recent applicants and trends over time. |
| 16 | Recommendations | B — Skill tags | Recommend jobs using skill-tag overlap between candidate profiles and job postings; no AI/ML required. |
| 17 | Job listing schema | C — Flexible | Structured fields (title, description, company, location, salary, job type, skills, experience, responsibilities, qualifications, benefits, remote policy, deadline, application method), plus company-defined custom sections. |
| 18 | CV management | B — Multiple CVs | Upload/manage/delete multiple CVs, set default and select CV per application. |
| 19 | Recruiter invitations | B — Team management | Invite by email, list team members, resend/revoke invitations and remove members. |
| 20 | Platform administration | B — Basic admin dashboard | Manage users, companies, jobs and applications; suspend accounts and remove inappropriate postings. |
| 21 | Duplicate applications | A — Prevent duplicates | One application per candidate per job; submitted applications cannot be edited. Guest email can help identify duplicates. |
| 22 | Withdrawals | B — Allow withdrawals | Registered candidates may withdraw anytime; recruiter sees Withdrawn; no reapplication to same job. |
| 23 | Email delivery | B — Background tasks | Queue emails asynchronously with retries; Celery and Redis are potential technologies, not yet finalized. |
| 24 | Client platforms | A — Responsive web | Single desktop/tablet/mobile responsive website; no PWA or native mobile app for MVP. |
| 25 | Architecture | B — Django REST + React | Django REST Framework backend, React frontend, PostgreSQL database. |
