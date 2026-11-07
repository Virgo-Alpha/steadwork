# Local Grafana on-call runner

The runner polls Grafana's built-in Alertmanager API every minute, deduplicates by fingerprint, and captures the alert, recent commits, Prometheus metrics, Loki events, and linked Tempo traces. By default it starts the bundled headless Codex CLI adapter through a provider-neutral JSON contract. Set `ONCALL_AGENT_COMMAND` to override it with another adapter. A verified low-risk backend fix is independently tested, committed on an alert-specific local branch, fast-forwarded into `main`, and pushed to `origin`. The runner then waits for the `CI` workflow's development deployment, checks the development health endpoint, and waits for the alert and action-error signal to clear. Production promotion remains manual.

Automatic fixes are allowlisted to **Repeated application submission failures** in `local` or `development`. The local duplicate-registration smoke alert is triage-only. Fixes are limited to `backend/api/`, five files, and 300 changed lines. Auth, data model, database, migrations, infrastructure, deployment, CI, observability, and on-call automation changes escalate. A fix must include a reproduction and telemetry evidence and pass `cd backend && uv run pytest -q` before the runner creates its commit.

False-positive reasoning and every lifecycle transition are written to a private, ignored hash-chained JSONL audit log under `on-call-engineer/state/`. The folder also contains incident packets, provider output, temporary clones, and test logs; review it for sensitive alert data before sharing. The repository commit history records code changes. The audit is local to this machine and is not a remote immutable log.

Verify the local audit chain with `python3 on-call-engineer/poll.py --verify-audit`.

## Provider adapter contract

The poller defaults to [adapters/codex.py](adapters/codex.py), which runs `codex exec` non-interactively with ephemeral session storage, a workspace-write sandbox, and the runner's result schema. It replaces itself with the Codex process so the runner's timeout and output capture apply to that process. Codex CLI must be installed on `PATH` and authenticated locally (for example with `codex login`). Its default configured model is used unless `ONCALL_AGENT_MODEL` is set. See the [Codex CLI non-interactive mode documentation](https://learn.chatgpt.com/docs/non-interactive-mode).

`ONCALL_CODEX_SANDBOX` defaults to `workspace-write`. Setting it to `danger-full-access` runs Codex without the filesystem and network sandbox. The adapter uses non-interactive `codex exec` and does not pass an approval flag. Use full access only in a disposable environment for a deliberate local test; the agent can access files, credentials, and network available to the operating-system account. Codex documents this mode as suitable only for a controlled environment.

To use a different agent, set `ONCALL_AGENT_COMMAND` as a JSON argv array or simple command. Any adapter, including the bundled Codex one, must:

1. Reads the complete incident packet from the path in `ONCALL_INCIDENT_JSON` and may read the response schema in `ONCALL_RESULT_SCHEMA`.
2. Uses `ONCALL_WORKSPACE` as its only writable repository checkout.
3. Receives the incident prompt on stdin and writes exactly one JSON result to stdout: `decision` (`fix`, `false_positive`, or `escalate`), `summary`, `evidence_ids`, `reproduction`, and `risk`.
4. Does not commit or push. The runner validates scope and evidence, tests, commits, merges, and pushes.

The bundled adapter uses the Codex CLI's saved local authentication, so no provider API-key environment variable is required when that login is available. If using `CODEX_API_KEY` or a custom provider credential, name it explicitly in `ONCALL_AGENT_ENV_ALLOWLIST`; secrets are otherwise removed from the agent environment. GitHub, Grafana, cloud, and database credentials are never passed to the coding process. The bundled Codex adapter limits writes to the incident checkout with Codex's `workspace-write` sandbox. Custom adapters are responsible for providing an equivalent workspace-limited sandbox.

Optional configuration to pin the Codex model and label it in the audit:

```sh
export ONCALL_AGENT_MODEL='<codex-model-id>'
```

To override the default with a custom adapter:

```sh
export ONCALL_AGENT_PROVIDER=my-provider
export ONCALL_AGENT_MODEL=my-model
export ONCALL_AGENT_COMMAND='["python3", "/absolute/path/to/my_provider_adapter.py"]'
export ONCALL_AGENT_ENV_ALLOWLIST=MY_PROVIDER_API_KEY
```

See [agent-prompt.md](agent-prompt.md), [result.schema.json](result.schema.json), and [runbooks/application-submission-failures.md](runbooks/application-submission-failures.md).

## Requirements

- Start the local observability stack with `make run` or `make compose-up`; Grafana credentials are read from `observability/.env`.
- Install the Codex CLI and authenticate it locally, or configure a custom adapter using the contract above.
- Install `uv` and the backend test dependencies.
- Configure local Git credentials that can push directly to `main`, and ensure repository branch rules allow that identity to push. The runner uses a fast-forward only merge and never force-pushes.
- Install and authenticate GitHub CLI (`gh`) so the runner can verify the CI/development deployment after pushing.
- The local Grafana/Prometheus instance must monitor the same target whose recovery you expect to verify. The current Render deployment is not instrumented by this local stack, so a local alert may remain active after the remote development deploy; that is recorded as an escalation rather than reported as recovered.

## Run

List current firing alerts without invoking an agent:

```sh
python3 on-call-engineer/poll.py --once --dry-run
```

Handle each new firing alert once:

```sh
python3 on-call-engineer/poll.py --once
```

Poll continuously every minute (Ctrl+C stops it):

```sh
python3 on-call-engineer/poll.py
```

Starting continuous polling enables autonomous code changes and pushes to `main`.

| Environment variable | Default | Purpose |
| --- | --- | --- |
| `GRAFANA_URL` | `http://127.0.0.1:3000` | Grafana base URL |
| `GRAFANA_USER` | `admin` | Grafana username |
| `GRAFANA_PASSWORD` | `observability/.env` value | Override the password file |
| `PROMETHEUS_URL` | `http://127.0.0.1:9090` | Prometheus query API |
| `ONCALL_AGENT_COMMAND` | bundled Codex adapter | Optional command override for another provider adapter |
| `ONCALL_AGENT_PROVIDER` | `codex` | Audit label for the configured adapter |
| `ONCALL_AGENT_MODEL` | `codex-default` | Optional Codex model selection and audit label; otherwise Codex CLI chooses its configured default |
| `ONCALL_CODEX_SANDBOX` | `workspace-write` | Codex sandbox mode; `danger-full-access` removes filesystem and network restrictions |
| `ONCALL_AGENT_ENV_ALLOWLIST` | empty | Comma-separated provider credential variables passed to the adapter |
| `ONCALL_MAIN_BRANCH` | `main` | Branch the runner clones, fast-forward merges, and pushes |
| `ONCALL_DEVELOPMENT_HEALTH_URL` | development `/api/health/` URL | Post-deployment health probe |
| `ONCALL_RECOVERY_TIMEOUT_SECONDS` | `1200` | Maximum wait for alert and action-error recovery |
| `ONCALL_RECOVERY_POLL_SECONDS` | `30` | Poll interval during recovery verification |

## Local evaluation

Run the included end-to-end evaluation with `python3 -m unittest discover -s on-call-engineer/eval -p 'test_*.py' -v`. It uses fake Grafana/Prometheus/Loki/Tempo APIs, a deterministic provider adapter, and a disposable local bare Git remote. The scenarios cover a false positive with no push and a controlled fix with backend tests, local push, health/recovery checks, and audit verification. `--test-mode` rejects non-local remotes and skips GitHub CI polling. Never inject a fault on `main`; see [manual-test.md](manual-test.md) for the isolated GitHub test branch procedure and its CI/deployment-wait limitation.

