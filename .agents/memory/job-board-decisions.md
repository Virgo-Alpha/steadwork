---
name: Job-board decisions
description: Confirmed product and architecture decisions for the tech job board.
---

The supplied scope confirms these product rules:
- Public browsing and guest applications are allowed; guests cannot track status.
- Authentication is email/password with verification and password reset, not social login.
- Candidate and company accounts are distinct; company accounts may have admins and recruiters.
- Job states are Draft, Published, Closed, and Expired. Application states include Applied, Under Review, Shortlisted, Rejected, Hired, and Withdrawn.
- Prevent duplicate applications per candidate/job; guest email can identify duplicates. Submitted applications cannot be edited, and a withdrawn application cannot be resubmitted.
- Companies can register without platform approval. Applications may be internal or external; external clicks are tracked separately from confirmed submissions.
- The selected backend target is Django REST Framework with PostgreSQL, while the current workspace API scaffold is Express with Drizzle.

**Why:** These choices define expected behavior and should not be lost when the mock frontend is connected to a real API.

**How to apply:** Preserve these constraints in service contracts, server validation, permissions, database design, and candidate/employer flows. Resolve the backend runtime mismatch before starting the real API implementation.
