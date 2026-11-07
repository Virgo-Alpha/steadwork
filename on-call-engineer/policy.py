"""Deterministic authorization gates for autonomous on-call changes."""

from __future__ import annotations

from typing import Any


AUTO_FIX_ALERTS = {"Repeated application submission failures"}
TRIAGE_ONLY_ALERTS = {"Local smoke test - duplicate registrations"}
AUTO_FIX_ENVIRONMENTS = {"local", "development"}
ALLOWED_CHANGE_ROOTS = ("backend/api/",)
PROTECTED_PATHS = (
    ".github/",
    "deployment/",
    "observability/",
    "on-call-engineer/",
    "backend/migrations/",
)
PROTECTED_FILES = {
    "Makefile",
    "docker-compose.yaml",
    "backend/api/auth.py",
    "backend/api/database.py",
    "backend/api/models.py",
    "backend/api/orm.py",
    "backend/api/repositories.py",
}
MAX_CHANGED_FILES = 5
MAX_CHANGED_LINES = 300


def alert_environment(alert: dict[str, Any]) -> str:
    labels = alert.get("labels") if isinstance(alert.get("labels"), dict) else {}
    annotations = alert.get("annotations") if isinstance(alert.get("annotations"), dict) else {}
    return str(labels.get("deployment_environment_name") or annotations.get("environment") or "").lower()


def authorization(alert: dict[str, Any]) -> tuple[bool, str]:
    labels = alert.get("labels") if isinstance(alert.get("labels"), dict) else {}
    name = str(labels.get("alertname") or "unnamed-alert")
    environment = alert_environment(alert)
    if name in TRIAGE_ONLY_ALERTS:
        return False, "This smoke-test alert is triage-only; code changes are not authorized."
    if name not in AUTO_FIX_ALERTS:
        return False, f"Alert {name!r} is not on the autonomous-fix allowlist."
    if environment not in AUTO_FIX_ENVIRONMENTS:
        return False, f"Automatic fixes are disabled for environment {environment or 'unknown'!r}."
    return True, "Allowlisted application failure in a non-production environment."


def validate_change_scope(
    paths: list[str], changed_lines: int, *, added_test_paths: set[str] | None = None
) -> str | None:
    if not paths:
        return "The proposed fix contains no committed files."
    if len(paths) > MAX_CHANGED_FILES:
        return f"Change touches {len(paths)} files; the limit is {MAX_CHANGED_FILES}."
    if changed_lines > MAX_CHANGED_LINES:
        return f"Change contains {changed_lines} changed lines; the limit is {MAX_CHANGED_LINES}."
    for path in paths:
        if path in PROTECTED_FILES or path.startswith(PROTECTED_PATHS):
            return f"Change touches protected path {path}."
        if not path.startswith(ALLOWED_CHANGE_ROOTS):
            return f"Change is outside the allowed backend application scope: {path}."
        if path.startswith("backend/api/tests/") and path not in (added_test_paths or set()):
            return f"Existing tests cannot be modified automatically: {path}."
    return None

