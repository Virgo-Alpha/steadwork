"""Business activity telemetry and durable history tests."""

import pytest
from datetime import datetime, timedelta, timezone
from rest_framework.test import APIClient

from api import telemetry
from api.orm import ActivityEventRecord, CompanyRecord, JobRecord, SavedJobRecord, UserRecord
from api.store import get_store, reset_store
from api.repositories import SQLAlchemyStoreRepository, create_database
from api.tests.migration_helpers import upgrade_database


class RecordingCounter:
    def __init__(self):
        self.measurements = []

    def add(self, amount, attributes):
        self.measurements.append((amount, attributes))


@pytest.fixture(autouse=True)
def clean_store():
    reset_store()
    yield
    reset_store()


def login(client, email, password):
    response = client.post(
        "/api/auth/login/", {"email": email, "password": password}, format="json"
    )
    assert response.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.json()['access_token']}")


def test_registration_and_successful_login_are_recorded_without_identity_metric_labels(monkeypatch):
    counter = RecordingCounter()
    monkeypatch.setattr(telemetry, "business_event_counter", counter)
    client = APIClient()

    registered = client.post(
        "/api/auth/register/",
        {"name": "Activity Candidate", "email": "activity@example.test",
         "password": "secure-password", "role": "candidate"},
        format="json",
    )
    assert registered.status_code == 201
    client.credentials()
    assert client.post(
        "/api/auth/login/",
        {"email": "activity@example.test", "password": "secure-password"},
        format="json",
    ).status_code == 200
    assert client.post(
        "/api/auth/login/",
        {"email": "activity@example.test", "password": "wrong-password"},
        format="json",
    ).status_code == 401

    events = get_store().activity_events
    assert [event.event_type for event in events] == ["user_registered", "login_succeeded"]
    assert events[0].actor_user_id == registered.json()["user"]["id"]
    assert counter.measurements == [
        (1, {"event": "user_registered", "role": "candidate", "application_method": "none", "origin": "live"}),
        (1, {"event": "login_succeeded", "role": "candidate", "application_method": "none", "origin": "live"}),
    ]
    assert all("user_id" not in attributes and "job_id" not in attributes
               for _, attributes in counter.measurements)


def test_domain_events_only_count_real_publish_application_rejection_withdrawal_and_save_changes(monkeypatch):
    counter = RecordingCounter()
    monkeypatch.setattr(telemetry, "business_event_counter", counter)
    candidate = APIClient()
    recruiter = APIClient()
    login(candidate, "candidate@example.com", "candidate-password")
    login(recruiter, "recruiter@example.com", "recruiter-password")

    created = recruiter.post(
        "/api/employer/jobs/",
        {"title": "Activity role", "description": "Role description", "location": "Remote",
         "deadline": "2099-01-01T00:00:00Z"},
        format="json",
    )
    assert created.status_code == 201
    job_id = created.json()["id"]
    assert recruiter.post(
        f"/api/employer/jobs/{job_id}/status/", {"status": "Published"}, format="json"
    ).status_code == 200

    body = {"jobId": "job-security", "candidateName": "Demo Candidate",
            "candidateEmail": "candidate@example.com", "cvName": "resume.pdf", "coverLetter": ""}
    submitted = candidate.post("/api/applications/", body, format="json")
    assert submitted.status_code == 201
    application_id = submitted.json()["id"]
    assert candidate.post(
        f"/api/applications/{application_id}/withdraw/", format="json"
    ).status_code == 200

    assert recruiter.post(
        "/api/employer/applications/application-1/status/", {"status": "Rejected"}, format="json"
    ).status_code == 200
    assert recruiter.post(
        "/api/employer/applications/application-1/status/", {"status": "Rejected"}, format="json"
    ).status_code == 200

    assert candidate.post("/api/saved-jobs/", {"jobId": "job-platform"}, format="json").status_code == 204
    assert candidate.post("/api/saved-jobs/", {"jobId": "job-platform"}, format="json").status_code == 204
    assert candidate.delete("/api/saved-jobs/job-platform/").status_code == 204

    event_types = [event.event_type for event in get_store().activity_events]
    assert event_types.count("job_published") == 1
    assert event_types.count("application_submitted") == 1
    assert event_types.count("application_withdrawn") == 1
    assert event_types.count("application_rejected") == 1
    assert event_types.count("job_saved") == 1
    assert event_types.count("job_unsaved") == 1


def test_external_apply_and_application_method_are_distinct_events(monkeypatch):
    counter = RecordingCounter()
    monkeypatch.setattr(telemetry, "business_event_counter", counter)
    response = APIClient().post(
        "/api/applications/guest/",
        {"jobId": "job-design", "candidateName": "Guest Candidate",
         "candidateEmail": "guest-activity@example.test", "cvName": "resume.pdf", "coverLetter": ""},
        format="json",
    )

    assert response.status_code == 201
    events = get_store().activity_events
    assert [event.event_type for event in events] == [
        "application_submitted", "external_apply_clicked"
    ]
    assert [attributes["event"] for _, attributes in counter.measurements] == [
        "application_submitted", "external_apply_clicked"
    ]
    assert all(attributes["application_method"] == "external"
               for _, attributes in counter.measurements)
    assert all(attributes["origin"] == "live" for _, attributes in counter.measurements)


def test_business_gauges_report_current_counts_and_rolling_activity_windows(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'business-gauges.sqlite3'}"
    upgrade_database(database_url)
    engine, session_factory = create_database(database_url)
    now = datetime.now(timezone.utc)
    with session_factory() as session:
        session.add_all([
            UserRecord(id="candidate-a", email="a@example.test", role="candidate", password_hash="x"),
            UserRecord(id="candidate-b", email="b@example.test", role="candidate", password_hash="x"),
            UserRecord(id="recruiter-a", email="r@example.test", role="recruiter", password_hash="x"),
            CompanyRecord(id="company-a", name="Test company"),
        ])
        session.flush()
        session.add_all([
            JobRecord(id="published", company_id="company-a", title="Published", status="Published"),
            JobRecord(id="draft", company_id="company-a", title="Draft", status="Draft"),
            SavedJobRecord(user_id="candidate-a", job_id="published"),
            ActivityEventRecord(id="login-a1", event_type="login_succeeded", occurred_at=now - timedelta(hours=1), actor_user_id="candidate-a", actor_role="candidate"),
            ActivityEventRecord(id="login-a2", event_type="login_succeeded", occurred_at=now - timedelta(hours=2), actor_user_id="candidate-a", actor_role="candidate"),
            ActivityEventRecord(id="login-b", event_type="login_succeeded", occurred_at=now - timedelta(days=3), actor_user_id="candidate-b", actor_role="candidate"),
            ActivityEventRecord(id="app-a1", event_type="application_submitted", occurred_at=now - timedelta(hours=1), actor_user_id="candidate-a", actor_role="candidate"),
            ActivityEventRecord(id="app-a2", event_type="application_submitted", occurred_at=now - timedelta(hours=2), actor_user_id="candidate-a", actor_role="candidate"),
            ActivityEventRecord(id="app-b", event_type="application_submitted", occurred_at=now - timedelta(days=3), actor_user_id="candidate-b", actor_role="candidate"),
        ])
        session.commit()

    try:
        result = telemetry._activity_gauge_values(engine, now=now)
    finally:
        engine.dispose()

    assert dict(result["users"]) == {"candidate": 2, "recruiter": 1}
    assert result["published_jobs"] == 1
    assert result["saved_jobs"] == 1
    assert result["active_users"] == {"24h": 1, "7d": 2}
    assert result["applications_per_active_candidate"] == {"24h": 2.0, "7d": 1.5}


def test_local_demo_seed_matches_tracked_business_events_and_is_time_distributed(monkeypatch):
    from api.store import _seed

    monkeypatch.setenv("STEADWORK_ENVIRONMENT", "development")
    monkeypatch.setenv("STEADWORK_SEED_OBSERVABILITY_DATA", "true")
    seed = _seed()

    demo_events = [event for event in seed.activity_events if event.origin == "demo"]
    event_types = {event.event_type for event in demo_events}
    assert {
        "user_registered", "login_succeeded", "job_published", "application_submitted",
        "application_withdrawn", "application_rejected", "external_apply_clicked",
        "job_saved", "job_unsaved",
    } <= event_types
    assert any(event.occurred_at >= datetime.now(timezone.utc) - timedelta(hours=24) for event in demo_events)
    assert any(event.occurred_at < datetime.now(timezone.utc) - timedelta(hours=24) for event in demo_events)
    assert seed.saved_jobs
    assert all(event.actor_user_id in {user.id for user in seed.users} for event in demo_events)


def test_demo_activity_seed_is_disabled_outside_local_development(monkeypatch):
    from api.store import _seed

    monkeypatch.setenv("STEADWORK_ENVIRONMENT", "production")
    monkeypatch.setenv("STEADWORK_SEED_OBSERVABILITY_DATA", "true")

    assert not [event for event in _seed().activity_events if event.origin == "demo"]


def test_database_seed_exposes_demo_and_live_activity_in_rolling_gauges(monkeypatch, tmp_path):
    monkeypatch.setenv("STEADWORK_ENVIRONMENT", "development")
    monkeypatch.setenv("STEADWORK_SEED_OBSERVABILITY_DATA", "true")
    database_url = f"sqlite:///{tmp_path / 'seeded-business-gauges.sqlite3'}"
    upgrade_database(database_url)
    engine, session_factory = create_database(database_url)
    try:
        with session_factory() as session:
            SQLAlchemyStoreRepository(session).load()
            session.commit()
        result = telemetry._activity_gauge_values(engine)
    finally:
        engine.dispose()

    assert {event["origin"] for event in result["rolling_business_events"]["24h"]} == {"demo"}
    assert {event["origin"] for event in result["rolling_business_events"]["7d"]} == {"demo"}
    assert {event["event"] for event in result["rolling_business_events"]["24h"]} >= {
        "login_succeeded", "application_submitted", "job_published",
    }
    assert {action["action"] for action in result["rolling_user_actions"]["24h"]} >= {
        "login", "register", "submit_application", "job_status",
    }
    assert {action["origin"] for action in result["rolling_user_actions"]["24h"]} == {"demo"}


def test_existing_local_database_gets_demo_activity_once(monkeypatch, tmp_path):
    from api.store import _seed

    monkeypatch.setenv("STEADWORK_ENVIRONMENT", "development")
    monkeypatch.setenv("STEADWORK_SEED_OBSERVABILITY_DATA", "false")
    database_url = f"sqlite:///{tmp_path / 'existing-local-seed.sqlite3'}"
    upgrade_database(database_url)
    engine, session_factory = create_database(database_url)
    try:
        with session_factory() as session:
            SQLAlchemyStoreRepository(session).replace(_seed())
            session.commit()

        monkeypatch.setenv("STEADWORK_SEED_OBSERVABILITY_DATA", "true")
        with session_factory() as session:
            SQLAlchemyStoreRepository(session).load()
            session.commit()
        with session_factory() as session:
            first_event_count = session.query(ActivityEventRecord).filter_by(origin="demo").count()
            first_saved_job_count = session.query(SavedJobRecord).count()
            SQLAlchemyStoreRepository(session).load()
            session.commit()
        with session_factory() as session:
            assert session.query(ActivityEventRecord).filter_by(origin="demo").count() == first_event_count
            assert session.query(SavedJobRecord).count() == first_saved_job_count
            assert first_event_count > 0
            assert first_saved_job_count == 1
    finally:
        engine.dispose()

