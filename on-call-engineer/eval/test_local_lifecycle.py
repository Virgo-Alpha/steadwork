"""End-to-end on-call lifecycle eval against a fake Grafana and local bare remote."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[2]
FAKE_PROVIDER = Path(__file__).with_name("fake_provider.py")


class EvalHandler(BaseHTTPRequestHandler):
    alert_reads = 0
    marker_path: Path | None = None
    alert = {
        "fingerprint": "eval-fingerprint-001",
        "status": {"state": "active"},
        "labels": {
            "alertname": "Repeated application submission failures",
            "service_name": "steadwork-api",
            "deployment_environment_name": "development",
            "service_version": "eval-version",
            "severity": "warning",
        },
        "annotations": {
            "summary": "Controlled evaluation alert",
            "environment": "development",
            "service": "steadwork-api",
        },
        "values": {"A": 3},
    }

    def log_message(self, *_args):
        pass

    def _send(self, value, status=200):
        body = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path.endswith("/api/alertmanager/grafana/api/v2/alerts"):
            type(self).alert_reads += 1
            self._send([type(self).alert] if type(self).alert_reads <= 2 else [])
            return
        if path.endswith("/loki/loki/api/v1/query_range"):
            self._send(
                {
                    "status": "success",
                    "data": {
                        "result": [
                            {
                                "values": [
                                    [
                                        "1",
                                        "user_action_failed trace_id=0123456789abcdef0123456789abcdef span_id=0123456789abcdef action=submit_application outcome=server_error",
                                    ]
                                ]
                            }
                        ]
                    },
                }
            )
            return
        if "/api/datasources/proxy/uid/tempo/api/traces/" in path:
            self._send({"batches": [{"spans": [{"name": "application.submit"}]}]})
            return
        if path.endswith("/api/v1/query_range"):
            marker_exists = bool(type(self).marker_path and type(self).marker_path.exists())
            query = urlsplit(self.path).query
            value = "0" if marker_exists else ("0.99" if "clamp_min" in query else "3")
            self._send(
                {
                    "status": "success",
                    "data": {"resultType": "matrix", "result": [{"values": [["1", value]]}]},
                }
            )
            return
        if path == "/health":
            self._send({"status": "ok", "service": "eval"})
            return
        self._send({"error": "not found", "path": path}, status=404)


def git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def make_remote(root: Path) -> tuple[Path, Path]:
    source = root / "source"
    bare = root / "origin.git"
    backend = source / "backend"
    (backend / "api" / "tests").mkdir(parents=True)
    (backend / "api" / "__init__.py").write_text("", encoding="utf-8")
    (backend / "api" / "bug.py").write_text('def behavior():\n    return "broken"\n', encoding="utf-8")
    (source / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    (backend / "api" / "tests" / "test_bug.py").write_text(
        "import unittest\n\nfrom api.bug import behavior\n\n\nclass ControlledBugTest(unittest.TestCase):\n    def test_controlled_bug(self):\n        self.assertEqual(behavior(), 'fixed')\n",
        encoding="utf-8",
    )
    (backend / "pyproject.toml").write_text(
        "[project]\nname = 'oncall-eval-backend'\nversion = '0.1.0'\nrequires-python = '>=3.12'\n\n"
        "[tool.pytest.ini_options]\npythonpath = ['.']\ntestpaths = ['api/tests']\n",
        encoding="utf-8",
    )
    git(source, "init", "--initial-branch=main")
    git(source, "config", "user.name", "On-call eval")
    git(source, "config", "user.email", "oncall-eval@example.test")
    git(source, "add", ".")
    git(source, "commit", "-m", "seed disposable on-call repository")
    subprocess.run(["git", "init", "--bare", str(bare)], check=True, capture_output=True, text=True)
    git(source, "remote", "add", "origin", str(bare))
    git(source, "push", "-u", "origin", "main")
    return source, bare


class LocalLifecycleEval(unittest.TestCase):
    def run_scenario(self, scenario: str) -> tuple[dict, Path, Path]:
        with tempfile.TemporaryDirectory(prefix="steadwork-oncall-eval-") as temporary:
            temp_root = Path(temporary)
            source, bare = make_remote(temp_root)
            initial_head = subprocess.run(
                ["git", "--git-dir", str(bare), "rev-parse", "refs/heads/main"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            marker = temp_root / "agent-patched.marker"
            EvalHandler.alert_reads = 0
            EvalHandler.marker_path = marker
            server = ThreadingHTTPServer(("127.0.0.1", 0), EvalHandler)
            server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            server_thread.start()
            base_url = f"http://127.0.0.1:{server.server_port}"
            state_dir = temp_root / "state"
            env = os.environ.copy()
            env.update(
                {
                    "ONCALL_REPOSITORY": str(source),
                    "ONCALL_GIT_REMOTE": str(bare),
                    "ONCALL_TEST_MODE": "1",
                    "ONCALL_STATE_DIR": str(state_dir),
                    "ONCALL_AGENT_PROVIDER": "eval-fake",
                    "ONCALL_AGENT_MODEL": "deterministic",
                    "ONCALL_AGENT_COMMAND": json.dumps([sys.executable, str(FAKE_PROVIDER)]),
                    "ONCALL_AGENT_ENV_ALLOWLIST": "ONCALL_EVAL_SCENARIO,ONCALL_EVAL_MARKER",
                    "ONCALL_EVAL_SCENARIO": scenario,
                    "ONCALL_EVAL_MARKER": str(marker),
                    "ONCALL_TEST_BACKEND_COMMAND": json.dumps([sys.executable, "-m", "unittest", "discover", "-s", "api/tests", "-v"]),
                    "ONCALL_RECOVERY_TIMEOUT_SECONDS": "5",
                    "ONCALL_RECOVERY_POLL_SECONDS": "0",
                    "GRAFANA_URL": base_url,
                    "GRAFANA_USER": "eval",
                    "GRAFANA_PASSWORD": "eval",
                    "PROMETHEUS_URL": base_url,
                    "ONCALL_DEVELOPMENT_HEALTH_URL": base_url + "/health",
                }
            )
            try:
                run = subprocess.run(
                    [sys.executable, str(ROOT / "on-call-engineer" / "poll.py"), "--once", "--test-mode"],
                    cwd=ROOT,
                    env=env,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                subprocess.run(
                    [sys.executable, str(ROOT / "on-call-engineer" / "poll.py"), "--verify-audit"],
                    cwd=ROOT,
                    env=env,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                events = [json.loads(line) for line in (state_dir / "audit.jsonl").read_text().splitlines()]
                bare_head = subprocess.run(
                    ["git", "--git-dir", str(bare), "rev-parse", "refs/heads/main"],
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip()
                return {"events": events, "head": bare_head, "initial_head": initial_head, "marker": marker.exists(), "false_positive_file": (state_dir / "false-positives.jsonl").exists()}, state_dir, bare
            finally:
                server.shutdown()
                server.server_close()
                server_thread.join(timeout=2)

    def test_false_positive_is_audited_without_pushing(self):
        result, state_dir, _bare = self.run_scenario("false_positive")
        phases = [event["phase"] for event in result["events"]]
        self.assertIn("false_positive", phases)
        self.assertFalse(result["marker"])
        self.assertTrue(result["false_positive_file"])

    def test_controlled_fix_is_tested_pushed_and_recovery_verified(self):
        result, _state_dir, _bare = self.run_scenario("fix")
        phases = [event["phase"] for event in result["events"]]
        self.assertIn("code_pushed", phases, json.dumps(result["events"], indent=2))
        self.assertIn("development_health", phases)
        self.assertIn("recovery_confirmed", phases)
        self.assertTrue(result["marker"])
        self.assertNotEqual(result["head"], result["initial_head"])


if __name__ == "__main__":
    unittest.main()
