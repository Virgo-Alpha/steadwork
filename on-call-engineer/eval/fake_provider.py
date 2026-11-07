#!/usr/bin/env python3
"""Deterministic provider adapter used only by the disposable local eval."""

import json
import os
from pathlib import Path


incident = json.loads(Path(os.environ["ONCALL_INCIDENT_JSON"]).read_text(encoding="utf-8"))
scenario = os.environ.get("ONCALL_EVAL_SCENARIO", "false_positive")
if scenario == "fix":
    source = Path(os.environ["ONCALL_WORKSPACE"]) / "backend/api/bug.py"
    source.write_text('def behavior():\n    return "fixed"\n', encoding="utf-8")
    Path(os.environ["ONCALL_EVAL_MARKER"]).write_text("patched\n", encoding="utf-8")
    result = {
        "decision": "fix",
        "summary": "Corrected the controlled regression.",
        "evidence_ids": ["alert", "metric.action_server_errors"],
        "reproduction": "The baseline test expected behavior() to return fixed but observed broken.",
        "risk": "low",
    }
else:
    result = {
        "decision": "false_positive",
        "summary": "The synthetic alert is configured as an expected outcome.",
        "evidence_ids": ["alert"],
        "reproduction": "",
        "risk": "low",
    }
print(json.dumps(result))
