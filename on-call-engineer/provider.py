"""Provider-neutral subprocess contract for headless coding agents."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Protocol

PROMPT_FILE = Path(__file__).with_name("agent-prompt.md")

RESULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["decision", "summary", "evidence_ids", "reproduction", "risk"],
    "properties": {
        "decision": {"type": "string", "enum": ["fix", "false_positive", "escalate"]},
        "summary": {"type": "string", "minLength": 1},
        "evidence_ids": {"type": "array", "items": {"type": "string"}},
        "reproduction": {"type": "string"},
        "risk": {"type": "string", "enum": ["low", "medium", "high"]},
    },
}


class ProviderError(RuntimeError):
    pass


class AgentProvider(Protocol):
    name: str
    model: str

    def investigate(
        self, incident: dict[str, Any], workspace: Path, run_dir: Path, timeout: int
    ) -> dict[str, Any]: ...


def provider_prompt(incident: dict[str, Any]) -> str:
    template = PROMPT_FILE.read_text(encoding="utf-8")
    return template.replace("{{INCIDENT_JSON}}", json.dumps(incident, indent=2, sort_keys=True))


class CommandProvider:
    """Run any configured adapter that implements the stdin/stdout JSON contract.

    ONCALL_AGENT_COMMAND is a JSON argv array or a simple command string. The adapter
    reads the incident JSON from ONCALL_INCIDENT_JSON and edits ONCALL_WORKSPACE. It
    writes one AgentResult JSON object to stdout. Provider-specific CLIs belong inside
    the adapter, not in the alert poller.
    """

    def __init__(self, command: str | None = None, name: str | None = None, model: str | None = None):
        raw_command = command if command is not None else os.environ.get("ONCALL_AGENT_COMMAND", "")
        default_adapter = not raw_command.strip()
        if default_adapter:
            adapter = Path(__file__).with_name("adapters") / "codex.py"
            self.argv = [sys.executable, str(adapter)]
        else:
            self.argv = []
        try:
            if not default_adapter:
                parsed = json.loads(raw_command)
                self.argv = parsed if isinstance(parsed, list) else shlex.split(raw_command)
        except json.JSONDecodeError:
            self.argv = shlex.split(raw_command)
        if not self.argv or not all(isinstance(part, str) for part in self.argv):
            raise ProviderError("ONCALL_AGENT_COMMAND must be a command or JSON argv array.")
        executable = shutil.which(self.argv[0])
        if not executable:
            raise ProviderError(f"Agent adapter executable was not found: {self.argv[0]}")
        self.argv[0] = executable
        default_name = "codex" if default_adapter else "custom"
        default_model = "codex-default" if default_adapter else "unspecified"
        self.name = name or os.environ.get("ONCALL_AGENT_PROVIDER", default_name)
        self.model = model or os.environ.get("ONCALL_AGENT_MODEL", default_model)

    def investigate(
        self, incident: dict[str, Any], workspace: Path, run_dir: Path, timeout: int
    ) -> dict[str, Any]:
        incident_path = run_dir / "incident.json"
        incident_path.write_text(json.dumps(incident, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (run_dir / "result-schema.json").write_text(
            json.dumps(RESULT_SCHEMA, indent=2) + "\n", encoding="utf-8"
        )
        env = safe_provider_environment(incident_path, workspace, run_dir)
        try:
            result = subprocess.run(
                self.argv,
                cwd=workspace,
                env=env,
                input=provider_prompt(incident),
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise ProviderError(f"Agent adapter exceeded the {timeout}-second run limit.") from error
        (run_dir / "agent.stdout").write_text(result.stdout, encoding="utf-8")
        (run_dir / "agent.stderr").write_text(result.stderr, encoding="utf-8")
        if result.returncode:
            raise ProviderError(
                f"Agent adapter exited {result.returncode}; inspect this run's agent logs."
            )
        try:
            response = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise ProviderError("Agent adapter stdout was not one JSON object.") from error
        validate_result(response, incident)
        return response


def safe_provider_environment(incident_path: Path, workspace: Path, run_dir: Path) -> dict[str, str]:
    # Keep provider credentials only when explicitly named; never pass GitHub, Grafana,
    # cloud, database, or Git authentication to the coding process.
    allowlist = {item.strip() for item in os.environ.get("ONCALL_AGENT_ENV_ALLOWLIST", "").split(",") if item.strip()}
    env = {key: value for key, value in os.environ.items() if key in {"PATH", "HOME", "LANG", "LC_ALL", "TZ"} or key in allowlist}
    env.update(
        {
            "ONCALL_INCIDENT_JSON": str(incident_path),
            "ONCALL_WORKSPACE": str(workspace),
            "ONCALL_RESULT_SCHEMA": str(run_dir / "result-schema.json"),
            "ONCALL_AGENT_PROVIDER": os.environ.get(
                "ONCALL_AGENT_PROVIDER", "codex" if not os.environ.get("ONCALL_AGENT_COMMAND") else "custom"
            ),
            "ONCALL_AGENT_MODEL": os.environ.get(
                "ONCALL_AGENT_MODEL", "codex-default" if not os.environ.get("ONCALL_AGENT_COMMAND") else "unspecified"
            ),
            "ONCALL_CODEX_SANDBOX": os.environ.get("ONCALL_CODEX_SANDBOX", "workspace-write"),
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_SYSTEM": os.devnull,
        }
    )
    return env


def validate_result(response: Any, incident: dict[str, Any]) -> None:
    if not isinstance(response, dict):
        raise ProviderError("Agent response must be a JSON object.")
    required = {"decision", "summary", "evidence_ids", "reproduction", "risk"}
    if set(response) != required:
        raise ProviderError("Agent response does not match the required result fields.")
    if response["decision"] not in {"fix", "false_positive", "escalate"}:
        raise ProviderError("Agent returned an unsupported decision.")
    if response["risk"] not in {"low", "medium", "high"}:
        raise ProviderError("Agent returned an unsupported risk level.")
    if not isinstance(response["summary"], str) or not response["summary"].strip():
        raise ProviderError("Agent response omitted a summary.")
    if not isinstance(response["reproduction"], str) or not isinstance(response["evidence_ids"], list):
        raise ProviderError("Agent response omitted reproduction or evidence references.")
    available = {str(item.get("id")) for item in incident.get("evidence", []) if isinstance(item, dict)}
    if not all(isinstance(item, str) and item in available for item in response["evidence_ids"]):
        raise ProviderError("Agent cited an evidence ID that was not in the incident packet.")

