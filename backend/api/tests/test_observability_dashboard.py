"""Provisioned dashboard and observability guide acceptance checks."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_dashboard_contains_explicit_thirty_day_success_sli_and_seeded_activity_graphs():
    dashboard = json.loads(
        (ROOT / "observability/grafana/dashboards/steadwork-overview.json").read_text()
    )
    panels = dashboard["panels"]
    sli = next(panel for panel in panels if panel["title"] == "30-day request success SLI")
    assert sli["type"] == "stat"
    sli_query = sli["targets"][0]["expr"]
    assert 'http_status_code=~"5.."' in sli_query
    assert "http_server_duration_milliseconds_count" in sli_query
    assert "[30d]" in sli_query
    assert 'service_name="steadwork-api"' in sli_query
    assert 'deployment_environment_name=~"$environment"' in sli_query
    assert 'service_version=~"$version"' in sli_query
    assert "http_server_request_duration_seconds_count" not in sli_query
    assert "or vector(0)" in sli_query

    activity_graphs = {
        panel["title"]: panel
        for panel in panels
        if panel["title"] in {
            "Registrations and logins (rolling 24h)",
            "Applications submitted, withdrawn, rejected (rolling 24h)",
            "Job and saved-job activity (rolling 24h)",
        }
    }
    assert len(activity_graphs) == 3
    for panel in activity_graphs.values():
        query = panel["targets"][0]["expr"]
        assert "steadwork_business_events_rolling" in query
        assert 'origin=~"$origin"' in query

    action_graph = next(panel for panel in panels if panel["title"] == "Successful tracked actions (rolling 24h)")
    assert action_graph["type"] == "timeseries"
    assert "steadwork_user_actions_rolling" in action_graph["targets"][0]["expr"]


def test_observability_guide_explains_sli_formula_and_demo_data_limits():
    guide = (ROOT / "_docs/observability.md").read_text().lower()
    assert "1 - (5xx requests / eligible requests)" in guide
    assert "4xx" in guide
    assert "synthetic" in guide
    assert "does not affect the sli" in guide
