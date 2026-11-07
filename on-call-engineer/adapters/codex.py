#!/usr/bin/env python3
"""Run the Codex CLI headlessly using the on-call provider contract."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def main() -> int:
    codex = shutil.which("codex")
    if not codex:
        print("Codex CLI was not found on PATH; install and authenticate it first.", file=sys.stderr)
        return 127

    workspace = Path(os.environ.get("ONCALL_WORKSPACE", ".")).resolve()
    schema = Path(os.environ.get("ONCALL_RESULT_SCHEMA", ""))
    if not workspace.is_dir():
        print("ONCALL_WORKSPACE is not a directory.", file=sys.stderr)
        return 2
    if not schema.is_file():
        print("ONCALL_RESULT_SCHEMA does not point to the runner's JSON schema.", file=sys.stderr)
        return 2

    # Codex replaces this process so the runner's timeout and captured stdout/stderr
    # apply directly to the agent process. The runner owns all Git commits and pushes.
    sandbox = os.environ.get("ONCALL_CODEX_SANDBOX", "workspace-write")
    if sandbox not in {"workspace-write", "danger-full-access"}:
        print(
            "ONCALL_CODEX_SANDBOX must be 'workspace-write' or 'danger-full-access'.",
            file=sys.stderr,
        )
        return 2

    argv = [
        codex,
        "exec",
        "--ephemeral",
        "--sandbox",
        sandbox,
        "--output-schema",
        str(schema.resolve()),
    ]
    if sandbox == "danger-full-access":
        argv.extend(["--ask-for-approval", "never"])
    model = os.environ.get("ONCALL_AGENT_MODEL", "")
    if model and model not in {"unspecified", "codex-default"}:
        argv.extend(["--model", model])
    argv.append("-")
    os.chdir(workspace)
    os.execvpe(codex, argv, os.environ.copy())
    return 127


if __name__ == "__main__":
    raise SystemExit(main())
