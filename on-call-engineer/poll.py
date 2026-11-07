#!/usr/bin/env python3
"""Poll Grafana and run a provider-neutral, bounded on-call response."""

from __future__ import annotations

import argparse
import base64
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evidence import EvidenceCollector
from policy import MAX_CHANGED_LINES, MAX_CHANGED_FILES, alert_environment, authorization, validate_change_scope
from provider import CommandProvider, PROMPT_FILE, ProviderError


ROOT = Path(__file__).resolve().parents[1]
ONCALL_DIR = Path(__file__).resolve().parent
STATE_DIR = Path(os.environ.get("ONCALL_STATE_DIR", ONCALL_DIR / "state")).resolve()
STATE_FILE = STATE_DIR / "runner-state.json"
AUDIT_FILE = STATE_DIR / "audit.jsonl"
FALSE_POSITIVE_FILE = STATE_DIR / "false-positives.jsonl"
DEFAULT_GRAFANA_URL = "http://127.0.0.1:3000"
ALERTS_PATH = "/api/alertmanager/grafana/api/v2/alerts"
AGENT_TIMEOUT_SECONDS = 3600
BACKEND_TEST_TIMEOUT_SECONDS = 1800
CI_TIMEOUT_SECONDS = 3600
RECOVERY_TIMEOUT_SECONDS = 1200
RECOVERY_POLL_SECONDS = 30
RECOVERY_STABLE_POLLS = 3


class OnCallError(RuntimeError):
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def grafana_config() -> tuple[str, str, str, str]:
    file_values = parse_env_file(ROOT / "observability" / ".env")
    base_url = os.environ.get("GRAFANA_URL", DEFAULT_GRAFANA_URL).rstrip("/")
    username = os.environ.get("GRAFANA_USER", file_values.get("GRAFANA_ADMIN_USER", "admin"))
    password = os.environ.get("GRAFANA_PASSWORD", file_values.get("GRAFANA_ADMIN_PASSWORD", ""))
    if not password:
        raise OnCallError("Set GRAFANA_PASSWORD or configure observability/.env.")
    parsed = urllib.parse.urlsplit(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise OnCallError("GRAFANA_URL must be an http(s) URL.")
    if parsed.username or parsed.password:
        raise OnCallError("Put Grafana credentials in GRAFANA_USER/GRAFANA_PASSWORD, not in GRAFANA_URL.")
    auth_header = "Basic " + base64.b64encode(f"{username}:{password}".encode()).decode("ascii")
    return base_url, username, password, auth_header


def api_json(url: str, auth_header: str | None = None, timeout: int = 15) -> Any:
    headers = {"Accept": "application/json"}
    if auth_header:
        headers["Authorization"] = auth_header
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def is_firing(alert: dict[str, Any]) -> bool:
    status = alert.get("status")
    state = status.get("state") if isinstance(status, dict) else status
    return str(state).lower() in {"active", "firing"}


def alert_fingerprint(alert: dict[str, Any]) -> str:
    fingerprint = alert.get("fingerprint")
    if fingerprint:
        return str(fingerprint)
    labels = alert.get("labels") if isinstance(alert.get("labels"), dict) else {}
    encoded = json.dumps(labels, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()[:16]


def alert_name(alert: dict[str, Any]) -> str:
    labels = alert.get("labels") if isinstance(alert.get("labels"), dict) else {}
    return str(labels.get("alertname") or "unnamed-alert")


def fetch_alerts(*, include_silenced: bool = False) -> list[dict[str, Any]]:
    base_url, _, _, auth_header = grafana_config()
    query = ""
    if not include_silenced:
        query = "?" + urllib.parse.urlencode(
            {"active": "true", "silenced": "false", "inhibited": "false"}
        )
    try:
        payload = api_json(f"{base_url}{ALERTS_PATH}{query}", auth_header)
    except urllib.error.HTTPError as error:
        raise OnCallError(f"Grafana alert API returned HTTP {error.code}.") from error
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise OnCallError(f"Could not read Grafana alerts: {error}") from error
    if not isinstance(payload, list):
        raise OnCallError("Grafana alert API response was not a JSON array.")
    return [item for item in payload if isinstance(item, dict) and is_firing(item)]


def save_state(state: dict[str, Any]) -> None:
    STATE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    STATE_DIR.chmod(0o700)
    temporary = STATE_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, STATE_FILE)
    STATE_FILE.chmod(0o600)


def load_state() -> dict[str, Any]:
    if not STATE_FILE.exists():
        return {"active": {}}
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise OnCallError(f"Could not read local runner state: {error}") from error
    if not isinstance(state, dict) or not isinstance(state.get("active"), dict):
        raise OnCallError("Local runner state has an invalid format.")
    return state


class AuditLog:
    """Private JSONL journal with a hash chain to expose accidental edits."""

    def __init__(self) -> None:
        STATE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
        STATE_DIR.chmod(0o700)

    def verify(self) -> None:
        if not AUDIT_FILE.exists():
            return
        previous_hash = None
        with AUDIT_FILE.open("r", encoding="utf-8") as stream:
            for index, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                record = json.loads(line)
                stored_hash = record.pop("record_hash", None)
                if record.get("previous_hash") != previous_hash:
                    raise OnCallError(f"Audit hash chain is broken at line {index}.")
                canonical = json.dumps(record, sort_keys=True, separators=(",", ":"))
                if stored_hash != hashlib.sha256(canonical.encode()).hexdigest():
                    raise OnCallError(f"Audit record hash does not match at line {index}.")
                previous_hash = stored_hash

    def append(self, event: dict[str, Any]) -> dict[str, Any]:
        previous_hash = None
        if AUDIT_FILE.exists():
            with AUDIT_FILE.open("rb") as stream:
                for line in stream:
                    if line.strip():
                        previous_hash = json.loads(line).get("record_hash")
        record = {"timestamp": now_iso(), **event, "previous_hash": previous_hash}
        canonical = json.dumps(record, sort_keys=True, separators=(",", ":"))
        record["record_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
        with AUDIT_FILE.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        if record.get("phase") == "false_positive":
            with FALSE_POSITIVE_FILE.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, sort_keys=True) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        AUDIT_FILE.chmod(0o600)
        if FALSE_POSITIVE_FILE.exists():
            FALSE_POSITIVE_FILE.chmod(0o600)
        return record


def run_command(
    command: list[str], *, cwd: Path, timeout: int = 120, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command, cwd=cwd, env=env, text=True, capture_output=True, timeout=timeout, check=False
        )
    except subprocess.TimeoutExpired as error:
        raise OnCallError(f"Command timed out: {command[0]}") from error
    if result.returncode:
        details = (result.stderr or result.stdout or "").strip()
        raise OnCallError(f"Command failed ({result.returncode}): {command[0]}\n{details[-3000:]}")
    return result


def git(repo: Path, *args: str, timeout: int = 120) -> str:
    return run_command(["git", *args], cwd=repo, timeout=timeout).stdout.strip()


def source_repository() -> Path:
    return Path(os.environ.get("ONCALL_REPOSITORY", ROOT)).resolve()


def source_remote() -> str:
    override = os.environ.get("ONCALL_GIT_REMOTE")
    if override:
        if os.environ.get("ONCALL_TEST_MODE") != "1":
            raise OnCallError("ONCALL_GIT_REMOTE is test-only; use --test-mode with a local bare remote.")
        return override
    try:
        return git(source_repository(), "remote", "get-url", "origin")
    except OnCallError as error:
        raise OnCallError("The source checkout must have an origin remote.") from error


def target_branch() -> str:
    return os.environ.get("ONCALL_MAIN_BRANCH", "main")


def safe_slug(value: str, limit: int = 40) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()[:limit] or "alert"


def create_checkout(run_dir: Path, alert: dict[str, Any]) -> tuple[Path, str, str]:
    remote = source_remote()
    branch = target_branch()
    repo_dir = run_dir / "repo"
    run_command(
        ["git", "clone", "--branch", branch, "--single-branch", remote, str(repo_dir)],
        cwd=run_dir,
        timeout=300,
    )
    base_sha = git(repo_dir, "rev-parse", "HEAD")
    alert_branch = f"oncall/{safe_slug(alert_name(alert))}-{hashlib.sha256(alert_fingerprint(alert).encode()).hexdigest()[:12]}"
    git(repo_dir, "checkout", "-b", alert_branch)
    git(repo_dir, "config", "user.name", "Steadwork On-Call Agent")
    git(repo_dir, "config", "user.email", "on-call-agent@users.noreply.github.com")
    return repo_dir, base_sha, alert_branch


def recent_changes(repo_dir: Path, base_sha: str) -> dict[str, Any]:
    log = git(repo_dir, "log", "-8", "--format=%H%x1f%ad%x1f%s", "--date=iso-strict", base_sha)
    commits = []
    for line in log.splitlines():
        parts = line.split("\x1f", 2)
        if len(parts) == 3:
            commits.append({"sha": parts[0], "timestamp": parts[1], "subject": parts[2]})
    return {"current_main_sha": base_sha, "recent_commits": commits}


def changed_paths(repo_dir: Path, base_sha: str) -> list[str]:
    output = git(repo_dir, "diff", "--name-only", base_sha)
    return [line for line in output.splitlines() if line]


def added_paths(repo_dir: Path, base_sha: str) -> set[str]:
    output = git(repo_dir, "diff", "--name-only", "--diff-filter=A", base_sha)
    return {line for line in output.splitlines() if line}


def changed_line_count(repo_dir: Path, base_sha: str) -> int:
    output = git(repo_dir, "diff", "--numstat", base_sha)
    total = 0
    for line in output.splitlines():
        parts = line.split("\t", 2)
        if len(parts) == 3:
            for value in parts[:2]:
                if value.isdigit():
                    total += int(value)
    return total


def working_tree_dirty(repo_dir: Path) -> bool:
    return bool(git(repo_dir, "status", "--porcelain"))


def commit_and_push(
    repo_dir: Path,
    branch: str,
    base_sha: str,
    alert: dict[str, Any],
    summary: str,
    test_log: Path,
) -> tuple[str, str, int]:
    paths = changed_paths(repo_dir, base_sha)
    line_count = changed_line_count(repo_dir, base_sha)
    reason = validate_change_scope(paths, line_count, added_test_paths=added_paths(repo_dir, base_sha))
    if reason:
        raise OnCallError(reason)
    if not working_tree_dirty(repo_dir):
        raise OnCallError("The agent reported a fix but produced no workspace changes.")
    if git(repo_dir, "rev-list", "--count", f"{base_sha}..HEAD") != "0":
        raise OnCallError("The agent must not create commits; the runner owns commits and pushes.")

    test_command = ["uv", "run", "pytest", "-q"]
    if os.environ.get("ONCALL_TEST_MODE") == "1" and os.environ.get("ONCALL_TEST_BACKEND_COMMAND"):
        test_command = json.loads(os.environ["ONCALL_TEST_BACKEND_COMMAND"])
    test = run_command(
        test_command,
        cwd=repo_dir / "backend",
        timeout=BACKEND_TEST_TIMEOUT_SECONDS,
        env=provider_safe_environment(),
    )
    test_log.write_text(test.stdout + test.stderr, encoding="utf-8")
    if working_tree_dirty(repo_dir) is False:
        raise OnCallError("The code change disappeared before commit.")
    git(repo_dir, "add", "--", *paths)
    commit_subject = f"on-call({safe_slug(alert_name(alert), 32)}): {safe_slug(summary, 48)}"
    git(repo_dir, "commit", "-m", commit_subject)
    if working_tree_dirty(repo_dir):
        raise OnCallError("The agent checkout is not clean after the runner commit.")
    commit_sha = git(repo_dir, "rev-parse", "HEAD")

    # Fail closed if main moved while the investigation or tests ran.
    git(repo_dir, "fetch", "origin", target_branch())
    remote_ref = f"origin/{target_branch()}"
    try:
        git(repo_dir, "merge-base", "--is-ancestor", remote_ref, branch)
    except OnCallError as error:
        raise OnCallError("Remote main advanced during investigation; fix was not pushed.") from error
    git(repo_dir, "checkout", target_branch())
    git(repo_dir, "merge", "--ff-only", branch)
    git(repo_dir, "push", "origin", target_branch())
    return commit_sha, commit_subject, line_count


def provider_safe_environment() -> dict[str, str]:
    # Test commands do not receive repository push credentials or monitoring secrets.
    env = os.environ.copy()
    for key in list(env):
        upper = key.upper()
        if upper.startswith(("GH_", "GITHUB_", "AWS_", "TF_", "GRAFANA_")) or upper.endswith(("_TOKEN", "_PASSWORD", "_SECRET")):
            env.pop(key, None)
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def metric_is_clear(collector: EvidenceCollector, alert: dict[str, Any]) -> bool:
    labels = alert.get("labels") if isinstance(alert.get("labels"), dict) else {}
    annotations = alert.get("annotations") if isinstance(alert.get("annotations"), dict) else {}
    service = str(labels.get("service_name") or annotations.get("service") or "steadwork-api")
    environment = str(labels.get("deployment_environment_name") or annotations.get("environment") or "")
    version = str(labels.get("service_version") or annotations.get("version") or "")
    evidence = collector.action_error_signal(service, environment, version)
    if evidence.get("status") != "available":
        return False
    results = evidence.get("data", {}).get("result", [])
    for series in results:
        for sample in series.get("values", []):
            try:
                if float(sample[1]) > 0:
                    return False
            except (ValueError, TypeError, IndexError):
                return False
    return True


def check_health(url: str) -> dict[str, Any]:
    if not url:
        return {"status": "unconfigured"}
    try:
        payload = api_json(url, timeout=10)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as error:
        return {"status": "unhealthy", "error": str(error)}
    if not isinstance(payload, dict) or payload.get("status") != "ok":
        return {"status": "unhealthy", "body": payload}
    return {"status": "healthy", "body": payload}


def wait_for_ci(commit_sha: str, timeout: int, *, test_mode: bool) -> dict[str, Any]:
    if test_mode:
        return {"status": "skipped_test_mode"}
    gh = shutil.which("gh")
    if not gh:
        return {"status": "unavailable", "error": "GitHub CLI (gh) is not installed."}
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            result = run_command(
                [gh, "run", "list", "--commit", commit_sha, "--json", "databaseId,status,conclusion,url,workflowName", "--limit", "20"],
                cwd=source_repository(),
                timeout=30,
            )
            runs = json.loads(result.stdout)
        except (OnCallError, json.JSONDecodeError) as error:
            return {"status": "unavailable", "error": str(error)}
        ci = next((run for run in runs if run.get("workflowName") == "CI"), None)
        if ci:
            if ci.get("status") == "completed":
                if ci.get("conclusion") != "success":
                    return {"status": "failed", "url": ci.get("url"), "conclusion": ci.get("conclusion")}
                try:
                    details = run_command(
                        [gh, "run", "view", str(ci["databaseId"]), "--json", "jobs"],
                        cwd=source_repository(),
                        timeout=30,
                    )
                    jobs = json.loads(details.stdout).get("jobs", [])
                except (OnCallError, json.JSONDecodeError):
                    return {"status": "unavailable", "url": ci.get("url"), "error": "Could not verify development job."}
                dev = next((job for job in jobs if "deploy development" in str(job.get("name", "")).lower()), None)
                if not dev or dev.get("conclusion") != "success":
                    return {"status": "failed", "url": ci.get("url"), "error": "Development deployment did not succeed."}
                return {"status": "success", "url": ci.get("url"), "run_id": ci.get("databaseId")}
        time.sleep(15)
    return {"status": "timeout", "error": f"CI/development deployment did not complete within {timeout} seconds."}


def verify_recovery(
    alert: dict[str, Any], collector: EvidenceCollector, timeout: int, *, test_mode: bool
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    stable = 0
    poll_seconds = int(os.environ.get("ONCALL_RECOVERY_POLL_SECONDS", RECOVERY_POLL_SECONDS))
    last_observation: dict[str, Any] = {}
    while time.monotonic() < deadline:
        try:
            active = fetch_alerts(include_silenced=True)
        except OnCallError as error:
            return {"status": "unverified", "reason": str(error)}
        same_alert_active = any(alert_fingerprint(item) == alert_fingerprint(alert) for item in active)
        metric_clear = metric_is_clear(collector, alert)
        last_observation = {"same_alert_active": same_alert_active, "action_error_metric_clear": metric_clear}
        if not same_alert_active and metric_clear:
            stable += 1
            if stable >= RECOVERY_STABLE_POLLS:
                return {"status": "recovered", "observations": stable, **last_observation}
        else:
            stable = 0
        time.sleep(poll_seconds)
    return {"status": "not_recovered", "observations": stable, **last_observation}


def test_mode_remote(remote: str, *, enabled: bool = False) -> bool:
    enabled = enabled or os.environ.get("ONCALL_TEST_MODE") == "1"
    if not enabled:
        return False
    parsed = urllib.parse.urlsplit(remote)
    local_path = Path(parsed.path if parsed.scheme == "file" else remote)
    if parsed.scheme not in {"", "file"} or not local_path.exists():
        raise OnCallError("ONCALL_TEST_MODE requires ONCALL_GIT_REMOTE to be a local bare repository path.")
    return True


def audit_context(alert: dict[str, Any], run_id: str, provider_name: str, model: str) -> dict[str, Any]:
    labels = alert.get("labels") if isinstance(alert.get("labels"), dict) else {}
    annotations = alert.get("annotations") if isinstance(alert.get("annotations"), dict) else {}
    return {
        "incident_id": run_id,
        "fingerprint": alert_fingerprint(alert),
        "alertname": alert_name(alert),
        "service": labels.get("service_name") or annotations.get("service"),
        "environment": alert_environment(alert),
        "service_version": labels.get("service_version") or annotations.get("version"),
        "provider": provider_name,
        "model": model,
        "prompt_sha256": hashlib.sha256(PROMPT_FILE.read_bytes()).hexdigest(),
    }


def run_incident(alert: dict[str, Any], audit: AuditLog, *, test_mode: bool = False) -> dict[str, Any]:
    name = safe_slug(alert_name(alert))
    fingerprint = alert_fingerprint(alert)
    short_hash = hashlib.sha256(fingerprint.encode()).hexdigest()[:12]
    run_id = f"{int(time.time())}-{name}-{short_hash}"
    run_dir = STATE_DIR / "runs" / run_id
    run_dir.mkdir(mode=0o700, parents=True, exist_ok=False)
    remote = source_remote()
    test_mode = test_mode_remote(remote, enabled=test_mode)
    policy_allowed, policy_reason = authorization(alert)
    provider_name = os.environ.get(
        "ONCALL_AGENT_PROVIDER", "codex" if not os.environ.get("ONCALL_AGENT_COMMAND") else "custom"
    )
    model = os.environ.get(
        "ONCALL_AGENT_MODEL", "codex-default" if not os.environ.get("ONCALL_AGENT_COMMAND") else "unspecified"
    )
    common = audit_context(alert, run_id, provider_name, model)
    audit.append({**common, "phase": "alert_observed", "run_dir": str(run_dir)})

    try:
        if not test_mode:
            gh = shutil.which("gh")
            if not gh:
                raise OnCallError("GitHub CLI is required to verify CI and development deployment before recovery.")
            run_command([gh, "auth", "status"], cwd=source_repository(), timeout=30)
        repo_dir, base_sha, branch = create_checkout(run_dir, alert)
        git_context = recent_changes(repo_dir, base_sha)
        base_url, _, _, auth_header = grafana_config()
        collector = EvidenceCollector(base_url, auth_header)
        context = collector.collect(alert, git_context)
        incident = {
            **common,
            "alert": alert,
            "context": {key: value for key, value in context.items() if key != "evidence"},
            "policy": {
                "automatic_fix_authorized": policy_allowed,
                "authorization_reason": policy_reason,
                "allowed_path_prefixes": ["backend/api/"],
                "protected_paths": ["security/authentication modules", "models/ORM/database", "migrations", "deployment", "observability", "CI", "on-call automation"],
                "max_changed_files": MAX_CHANGED_FILES,
                "max_changed_lines": MAX_CHANGED_LINES,
                "production_changes": False,
            },
            "evidence": context["evidence"],
        }
        incident_path = run_dir / "incident.json"
        incident_path.write_text(json.dumps(incident, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        audit.append({**common, "phase": "context_collected", "evidence_ids": [item["id"] for item in context["evidence"]], "evidence_ready": context["evidence_ready"], "runbook_url": context.get("runbook_url"), "base_sha": base_sha})
        if not context["evidence_ready"]:
            record = audit.append({**common, "phase": "escalated", "reason": "No Prometheus or Loki evidence source was available.", "base_sha": base_sha})
            return {"result": "escalated", "record_hash": record["record_hash"], "run_dir": str(run_dir)}

        audit.append({**common, "phase": "investigation_started", "base_sha": base_sha, "authorization": policy_reason})
        provider = CommandProvider()
        provider_name, model = provider.name, provider.model
        common.update({"provider": provider_name, "model": model})
        response = provider.investigate(incident, repo_dir, run_dir, AGENT_TIMEOUT_SECONDS)
        evidence_ids = response["evidence_ids"]
        audit.append({**common, "phase": "investigation_completed", "decision": response["decision"], "summary": response["summary"], "evidence_ids": evidence_ids, "reproduction": response["reproduction"], "risk": response["risk"], "base_sha": base_sha})

        decision = response["decision"]
        if decision == "false_positive":
            if "alert" not in evidence_ids:
                raise OnCallError("A false-positive classification must cite the alert evidence.")
            if working_tree_dirty(repo_dir) or git(repo_dir, "rev-list", "--count", f"{base_sha}..HEAD") != "0":
                raise OnCallError("Provider reported false positive but changed the checkout.")
            record = audit.append({**common, "phase": "false_positive", "reasoning": response["summary"], "evidence_ids": evidence_ids, "base_sha": base_sha})
            return {"result": "false_positive", "record_hash": record["record_hash"], "run_dir": str(run_dir)}
        if decision == "escalate":
            record = audit.append({**common, "phase": "escalated", "reason": response["summary"], "evidence_ids": evidence_ids, "base_sha": base_sha})
            return {"result": "escalated", "record_hash": record["record_hash"], "run_dir": str(run_dir)}
        if not policy_allowed:
            raise OnCallError(f"Provider proposed a fix without authorization: {policy_reason}")
        if response["risk"] != "low" or not response["reproduction"].strip():
            raise OnCallError("A fix requires a concrete reproduction and low risk classification.")
        telemetry_ids = {item["id"] for item in context["evidence"] if item.get("kind") in {"prometheus", "loki"} and item.get("status") == "available"}
        if "alert" not in evidence_ids or not telemetry_ids.intersection(evidence_ids):
            raise OnCallError("A fix must cite the alert and at least one available telemetry evidence item.")
        paths = changed_paths(repo_dir, base_sha)
        scope_error = validate_change_scope(paths, changed_line_count(repo_dir, base_sha))
        if scope_error:
            raise OnCallError(scope_error)
        audit.append({**common, "phase": "response_authorized", "reason": policy_reason, "paths": paths, "changed_lines": changed_line_count(repo_dir, base_sha)})

        # Re-check that the same alert is still firing before authorizing a push.
        if not any(alert_fingerprint(item) == fingerprint for item in fetch_alerts()):
            record = audit.append({**common, "phase": "escalated", "reason": "Alert resolved before the fix passed authorization; no commit pushed.", "paths": paths})
            return {"result": "escalated", "record_hash": record["record_hash"], "run_dir": str(run_dir)}

        test_log = run_dir / "backend-tests.log"
        try:
            pushed_sha, commit_subject, line_count = commit_and_push(repo_dir, branch, base_sha, alert, response["summary"], test_log)
            audit.append({**common, "phase": "code_pushed", "commit_sha": pushed_sha, "commit_subject": commit_subject, "paths": paths, "changed_lines": line_count, "test_command": "cd backend && uv run pytest -q", "test_result": "passed", "test_log": str(test_log)})
        except OnCallError as error:
            if test_log.exists():
                details = test_log.read_text(encoding="utf-8")[-2000:]
            else:
                details = str(error)
            record = audit.append({**common, "phase": "escalated", "reason": details, "paths": paths, "test_result": "failed_or_push_blocked"})
            return {"result": "escalated", "record_hash": record["record_hash"], "run_dir": str(run_dir)}

        ci = wait_for_ci(pushed_sha, CI_TIMEOUT_SECONDS, test_mode=test_mode)
        audit.append({**common, "phase": "development_deployment", "commit_sha": pushed_sha, "deployment": ci})
        if ci["status"] not in {"success", "skipped_test_mode"}:
            record = audit.append({**common, "phase": "escalated", "reason": "CI/development deployment failed or could not be verified.", "deployment": ci, "commit_sha": pushed_sha})
            return {"result": "escalated", "record_hash": record["record_hash"], "run_dir": str(run_dir)}

        health_url = os.environ.get("ONCALL_DEVELOPMENT_HEALTH_URL", "https://steadwork-development.onrender.com/api/health/")
        if test_mode and "ONCALL_DEVELOPMENT_HEALTH_URL" not in os.environ:
            health = {"status": "skipped_test_mode"}
        else:
            health = check_health(health_url)
        audit.append({**common, "phase": "development_health", "url": health_url if health["status"] != "skipped_test_mode" else None, "health": health})
        if health["status"] not in {"healthy", "skipped_test_mode"}:
            record = audit.append({**common, "phase": "escalated", "reason": "Development health check failed.", "health": health, "commit_sha": pushed_sha})
            return {"result": "escalated", "record_hash": record["record_hash"], "run_dir": str(run_dir)}

        recovery = verify_recovery(
            alert,
            collector,
            int(os.environ.get("ONCALL_RECOVERY_TIMEOUT_SECONDS", RECOVERY_TIMEOUT_SECONDS)),
            test_mode=test_mode,
        )
        audit.append({**common, "phase": "recovery_verification", "recovery": recovery, "commit_sha": pushed_sha})
        final_phase = "recovery_confirmed" if recovery["status"] == "recovered" else "escalated"
        record = audit.append({**common, "phase": final_phase, "reason": response["summary"] if final_phase == "recovery_confirmed" else "Fix was pushed but user-impact recovery was not confirmed.", "commit_sha": pushed_sha, "recovery": recovery, "deployment": ci, "paths": paths})
        return {"result": final_phase, "record_hash": record["record_hash"], "run_dir": str(run_dir)}
    except (OnCallError, ProviderError, OSError, ValueError) as error:
        record = audit.append({**common, "phase": "escalated", "reason": str(error), "run_dir": str(run_dir)})
        return {"result": "escalated", "record_hash": record["record_hash"], "run_dir": str(run_dir)}


def run_once(audit: AuditLog, *, dry_run: bool = False, test_mode: bool = False) -> None:
    alerts = fetch_alerts()
    state = load_state()
    active = state["active"]
    firing = {alert_fingerprint(alert): alert for alert in alerts}
    state["active"] = {fingerprint: item for fingerprint, item in active.items() if fingerprint in firing}
    if dry_run:
        print(f"Grafana reports {len(alerts)} firing, unsilenced alert(s).")
        for alert in alerts:
            print(f"- {alert_name(alert)} [{alert_fingerprint(alert)}]")
        return
    new_alerts = [alert for alert in alerts if alert_fingerprint(alert) not in state["active"]]
    save_state(state)
    if not new_alerts:
        print(f"No new firing alerts ({len(alerts)} currently active).")
        return
    for alert in new_alerts:
        fingerprint = alert_fingerprint(alert)
        state["active"][fingerprint] = {"status": "processing", "started_at": now_iso()}
        save_state(state)
        print(f"Handling {alert_name(alert)} [{fingerprint}]...")
        outcome = run_incident(alert, audit, test_mode=test_mode)
        state["active"][fingerprint] = {
            "status": outcome["result"],
            "started_at": state["active"][fingerprint]["started_at"],
            "finished_at": now_iso(),
            "run_dir": outcome.get("run_dir"),
            "audit_hash": outcome.get("record_hash"),
        }
        save_state(state)
        print(f"{outcome['result']} [{outcome.get('record_hash', 'no-audit-hash')}]")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument("--once", action="store_true", help="poll and process once")
    parser.add_argument("--dry-run", action="store_true", help="list alerts without invoking an agent")
    parser.add_argument("--test-mode", action="store_true", help="allow only a local bare Git remote and skip GitHub CI polling")
    parser.add_argument("--verify-audit", action="store_true", help="verify the local audit hash chain and exit")
    args = parser.parse_args()
    if args.poll_seconds < 1:
        parser.error("--poll-seconds must be at least 1")
    os.umask(0o077)
    if args.test_mode:
        os.environ["ONCALL_TEST_MODE"] = "1"
    STATE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock_path = STATE_DIR / "runner.lock"
    audit = AuditLog()
    try:
        audit.verify()
    except (OnCallError, json.JSONDecodeError) as error:
        print(f"Audit verification failed: {error}", file=sys.stderr)
        return 2
    if args.verify_audit:
        print("On-call audit hash chain is valid.")
        return 0
    with lock_path.open("w", encoding="utf-8") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("Another on-call poller already holds the runner lock.", file=sys.stderr)
            return 2
        if args.test_mode:
            try:
                test_mode_remote(source_remote(), enabled=True)
            except OnCallError as error:
                print(error, file=sys.stderr)
                return 2
        try:
            while True:
                try:
                    run_once(audit, dry_run=args.dry_run, test_mode=args.test_mode)
                except (OnCallError, urllib.error.URLError) as error:
                    print(f"On-call poll failed: {error}", file=sys.stderr)
                    if args.once:
                        return 1
                if args.once:
                    return 0
                time.sleep(args.poll_seconds)
        except KeyboardInterrupt:
            print("On-call polling stopped.")
            return 130


if __name__ == "__main__":
    raise SystemExit(main())
