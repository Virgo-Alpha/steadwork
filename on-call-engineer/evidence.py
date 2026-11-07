"""Read-only collection of alert, metric, log, trace, and deployment context."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any


def _quoted(value: str) -> str:
    return json.dumps(value)


class EvidenceCollector:
    def __init__(self, grafana_url: str, auth_header: str, prometheus_url: str | None = None):
        self.grafana_url = grafana_url.rstrip("/")
        self.auth_header = auth_header
        self.prometheus_url = (prometheus_url or os.environ.get("PROMETHEUS_URL", "http://127.0.0.1:9090")).rstrip("/")

    def _get_json(self, url: str, timeout: int = 15, grafana: bool = False) -> Any:
        headers = {"Accept": "application/json"}
        if grafana:
            headers["Authorization"] = self.auth_header
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def collect(self, alert: dict[str, Any], git_context: dict[str, Any]) -> dict[str, Any]:
        labels = alert.get("labels") if isinstance(alert.get("labels"), dict) else {}
        annotations = alert.get("annotations") if isinstance(alert.get("annotations"), dict) else {}
        service = str(labels.get("service_name") or annotations.get("service") or "steadwork-api")
        environment = str(labels.get("deployment_environment_name") or annotations.get("environment") or "")
        version = str(labels.get("service_version") or annotations.get("version") or "")
        now = int(time.time())
        evidence: list[dict[str, Any]] = [
            {"id": "alert", "kind": "grafana_alert", "status": "available", "data": alert},
            {"id": "change.recent_commits", "kind": "git_history", "status": "available", "data": git_context},
        ]

        labels_selector = f'service_name={_quoted(service)}'
        if environment:
            labels_selector += f',deployment_environment_name={_quoted(environment)}'
        if version:
            labels_selector += f',service_version={_quoted(version)}'
        metric_queries = {
            "metric.action_server_errors": (
                "sum(increase(steadwork_user_action_total{"
                + labels_selector
                + ',outcome="server_error"}[10m]))'
            ),
            "metric.http_5xx": (
                "sum(increase(http_server_duration_milliseconds_count{"
                + labels_selector
                + ',http_status_code=~"5.."}[10m]))'
            ),
            "metric.request_success_ratio": (
                "1 - ((sum(increase(http_server_duration_milliseconds_count{"
                + labels_selector
                + ',http_status_code=~"5.."}[10m])) or vector(0)) / clamp_min(sum(increase('
                + "http_server_duration_milliseconds_count{"
                + labels_selector
                + "}[10m])),1))"
            ),
        }
        for evidence_id, query in metric_queries.items():
            evidence.append(self._prometheus_evidence(evidence_id, query, now))

        logs = self._loki_evidence(service, environment, version, now)
        evidence.append(logs)
        trace_ids = sorted(
            {
                trace_id.lower()
                for line in logs.get("data", {}).get("lines", [])
                for trace_id in re.findall(r"trace_id=([0-9a-fA-F]{32})", str(line))
            }
        )[:3]
        for index, trace_id in enumerate(trace_ids, 1):
            evidence.append(self._tempo_evidence(f"trace.{index}", trace_id))

        return {
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "service": service,
            "environment": environment,
            "service_version": version,
            "runbook_url": annotations.get("runbook_url"),
            "dashboard_url": annotations.get("dashboard"),
            "evidence": evidence,
            "evidence_ready": any(
                item["status"] == "available"
                and item["id"] in {"metric.action_server_errors", "metric.http_5xx", "logs.action_events"}
                for item in evidence
            ),
        }

    def action_error_signal(self, service: str, environment: str, version: str) -> dict[str, Any]:
        selector = f'service_name={_quoted(service)},outcome="server_error"'
        if environment:
            selector += f',deployment_environment_name={_quoted(environment)}'
        if version:
            selector += f',service_version={_quoted(version)}'
        query = f"sum(increase(steadwork_user_action_total{{{selector}}}[10m]))"
        return self._prometheus_evidence("metric.action_server_errors", query, int(time.time()))

    def _prometheus_evidence(self, evidence_id: str, query: str, now: int) -> dict[str, Any]:
        params = urllib.parse.urlencode(
            {"query": query, "start": now - 600, "end": now, "step": "60s"}
        )
        try:
            data = self._get_json(f"{self.prometheus_url}/api/v1/query_range?{params}")
            if data.get("status") != "success":
                raise ValueError("Prometheus returned a non-success status")
            return {"id": evidence_id, "kind": "prometheus", "status": "available", "query": query, "data": data.get("data", {})}
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, json.JSONDecodeError) as error:
            return {"id": evidence_id, "kind": "prometheus", "status": "unavailable", "query": query, "error": str(error)}

    def _loki_evidence(self, service: str, environment: str, version: str, now: int) -> dict[str, Any]:
        selector = f'service_name={_quoted(service)}'
        if environment:
            selector += f',deployment_environment_name={_quoted(environment)}'
        if version:
            selector += f',service_version={_quoted(version)}'
        logql = "{" + selector + "} |= \"user_action_\""
        params = urllib.parse.urlencode(
            {
                "query": logql,
                "start": str((now - 600) * 1_000_000_000),
                "end": str(now * 1_000_000_000),
                "limit": "30",
                "direction": "backward",
            }
        )
        url = f"{self.grafana_url}/api/datasources/proxy/uid/loki/loki/api/v1/query_range?{params}"
        try:
            response = self._get_json(url, grafana=True)
            streams = response.get("data", {}).get("result", [])
            lines = [
                entry[1]
                for stream in streams
                for entry in stream.get("values", [])
                if isinstance(entry, list) and len(entry) > 1
            ][:30]
            return {"id": "logs.action_events", "kind": "loki", "status": "available", "query": logql, "data": {"lines": lines}}
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, json.JSONDecodeError) as error:
            return {"id": "logs.action_events", "kind": "loki", "status": "unavailable", "query": logql, "error": str(error)}

    def _tempo_evidence(self, evidence_id: str, trace_id: str) -> dict[str, Any]:
        url = f"{self.grafana_url}/api/datasources/proxy/uid/tempo/api/traces/{trace_id}"
        try:
            data = self._get_json(url, grafana=True)
            serialized = json.dumps(data, separators=(",", ":"))
            if len(serialized) > 20_000:
                serialized = serialized[:20_000] + "…[truncated]"
            return {"id": evidence_id, "kind": "tempo_trace", "status": "available", "trace_id": trace_id, "data": serialized}
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, json.JSONDecodeError) as error:
            return {"id": evidence_id, "kind": "tempo_trace", "status": "unavailable", "trace_id": trace_id, "error": str(error)}

