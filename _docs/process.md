# Delivery process

- Tasks are GitHub issues, one at a time per merge track.
- Read the acceptance criteria before starting and before closing.
- Keep the status of every issue visible in the backlog and GitHub.
- Commit regularly.

## Roles

- PM grooms a task before implementation and follows `_docs/team/pm.md`.
- Engineer implements one groomed task and follows
  `_docs/team/software-engineer.md`.
- QA verifies the result and follows `_docs/team/qa-engineer.md`.
- Reviewer is a fresh agent who reviews the implementation and acceptance
  criteria without being the implementer.
- The orchestrator coordinates work, but never implements an issue itself.

## Task status and dependency scheduling

The orchestrator maintains each task as one of `backlog`, `ready`, `grooming`,
`in_progress`, `review`, `changes_requested`, `approved`, `merged`, `blocked`
or `closed`. The GitHub issue state and the status in `_docs/tasks.md` must be
updated when a task changes phase.

Before scheduling an issue, inspect its acceptance criteria, constraints,
declared out-of-scope follow-ups and dependencies. A task is eligible only
when all prerequisite issues are merged and no active task owns a conflicting
file. Dependent tasks are queued sequentially; they are never started in
parallel merely because an agent slot is available.

The orchestrator keeps up to five agent slots full with eligible, independent
tracks. It groups work by file ownership and records each track's owned files.
If two tasks need the same file, shared configuration, schema, API contract or
generated output, schedule them sequentially or explicitly split ownership
before starting them. Prefer tasks with disjoint files and no behavioral
dependency.

The database, container, integration-test, CI and documentation tracks have
these sequencing rules:

- Backend skeleton precedes the in-memory backend and API implementation.
- Candidate/employer API work follows the auth/store foundation.
- Backend API integration follows the backend endpoints.
- Frontend/backend integration follows both the backend API and frontend
  adapter work.
- SQLite persistence follows the in-memory integration path; migrations follow
  the SQLAlchemy model work.
- PostgreSQL Compose follows migrations; the complete two-service container
  stack follows PostgreSQL Compose.
- Compose-backed E2E follows the container stack.
- The unified test command follows all test suites, including E2E.
- CI follows the unified test command.
- README and final E2E/documentation verification are end-of-track tasks and
  should be queued after the commands, container workflow and CI behavior are
  stable.

## Worktrees

Every active engineer and reviewer receives an isolated git worktree created
from the current main branch. The orchestrator records the worktree path,
branch, issue number, agent, owned files and status before the agent starts.
Agents do not work directly in the main checkout and do not share a worktree.

Before assigning a task, the orchestrator compares its owned-file set with
active tracks and checks for logical conflicts, including shared interfaces,
configuration, migrations, Compose files, generated clients and test fixtures.
A clean path list is not sufficient when two tasks change the same contract.
Move the task to `blocked` or queue it behind the conflicting track when a
logical conflict is found.

## Lifecycle

1. Select the next eligible issue whose dependencies are merged.
2. Groom it with the PM; do not silently drop out-of-scope work.
3. Create its isolated worktree and record file ownership.
4. Give the engineer the issue, acceptance criteria, constraints and worktree.
5. Require unit tests first, implementation, full relevant tests and a commit.
6. Send the completed work to a fresh reviewer in a separate worktree.
7. If review fails, return the findings to the same implementer and keep the
   issue in `changes_requested`; do not close or merge it.
8. When review passes, run QA against every acceptance criterion.
9. If QA fails, return the exact failure to the implementer and repeat review.
10. Merge one approved worktree into main, one issue at a time.
11. Run the relevant regression checks, update task/GitHub status, and remove
    the merged worktree only after the branch is no longer needed.
12. Recompute dependencies and conflicts before filling the next agent slot.

## Conflict resolution

- Never merge two branches concurrently.
- Rebase or merge the current main branch into a worktree only after checking
  for uncommitted changes and recording the operation.
- On a textual conflict, the implementer resolves it in the owning worktree,
  reruns tests, and requests a fresh review.
- On a logical conflict, the orchestrator pauses the later task, updates its
  scope or ownership, and queues it after the earlier task.
- Do not resolve conflicts by dropping another issue's acceptance criterion.
- If ownership cannot be made unambiguous, stop scheduling the affected tasks
  and ask the PM to split or groom them again.

## Rules

- The engineer does not close issues.
- QA does not fix code; it reports PASS or FAIL with commands and evidence.
- The reviewer does not implement fixes.
- The orchestrator closes an issue only after review and QA pass.
- E2E work belongs in the repository-root `e2e/` track and is scheduled near
  the end, after the Compose stack is stable.
- README work is scheduled at the end so it documents the final commands and
  behavior rather than assumptions.
