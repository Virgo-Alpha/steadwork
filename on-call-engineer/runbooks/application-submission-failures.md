# Repeated application submission failures

## Signal

The rule fires when at least three `submit_application` actions have outcome `server_error` during the last ten minutes and the condition remains true for five minutes. Expected `4xx` responses do not match this alert.

## Investigation

1. Confirm the alert's `service_name`, `deployment_environment_name`, and `service_version` labels. Compare that version with the recent commit list in the incident packet.
2. Review the `metric.action_server_errors`, `metric.http_5xx`, and `metric.request_success_ratio` evidence.
3. Inspect `logs.action_events` and open any linked Tempo traces by their `trace_id`. Use the `span_id` to identify the failing application span.
4. Reproduce with the existing backend tests or a local request in an isolated checkout. Do not use production data or credentials.

## Automatic response boundary

The local agent may change only low-risk files under `backend/api/`, with no more than five files or 300 changed lines. Authentication, persistence models, migrations, deployment, CI, observability, and on-call automation changes require escalation. The runner reruns `cd backend && uv run pytest -q` before it commits or pushes.

After the push, the runner waits for the `CI` workflow's development deployment job, checks the development `/api/health/` endpoint, and waits for the same Grafana alert and action-error signal to clear. If any stage fails or recovery is not observed within the configured window, it records an escalation. Production promotion remains manual.

## Expected behavior

The duplicate-registration smoke rule is intentionally excluded from automatic code changes. Duplicate-email responses are expected client-visible `409` outcomes and should be recorded as false positives when the local smoke rule is unpaused.
