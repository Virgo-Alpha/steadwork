# Repository guidance

Follow the modular documentation rather than placing all project guidance in
this file:

- `_docs/process.md` describes the issue lifecycle and orchestrator workflow.
- `_docs/task-template.md` is the template for grooming GitHub issues.
- `_docs/specs.md` contains the product and API specifications.
- `_docs/backend-plan.md` records backend assumptions and unresolved decisions.
- `_docs/team/pm.md` describes product-manager responsibilities.
- `_docs/team/software-engineer.md` describes implementation responsibilities.
- `_docs/team/qa-engineer.md` describes verification responsibilities.
- `_docs/tasks.md` is the backlog; each task is tracked as a GitHub issue.

For backend work, use uv for dependency management. Useful commands:

uv sync
uv add <PACKAGE-NAME>
uv run python <PYTHON-FILE>
