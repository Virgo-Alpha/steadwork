"""HTTP-level integration coverage against one temporary SQLite DB per test."""

from pathlib import Path

import pytest
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from sqlalchemy.engine import make_url
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from api.middleware import _database
from api.database import get_database_url
from api.orm import ApplicationRecord, JobRecord
from api.repositories import Repository
from api.tests.migration_helpers import upgrade_database


@pytest.fixture
def sqlite_api(tmp_path):
    database_path = tmp_path / "integration.sqlite3"
    database_url = f"sqlite:///{database_path}"
    default_database = Path(make_url(get_database_url({})).database)
    default_state = default_database.stat().st_mtime_ns if default_database.exists() else None
    _database.cache_clear()
    upgrade_database(database_url)
    with override_settings(STORE_BACKEND="sqlite", DATABASE_URL=database_url):
        try:
            yield APIClient(), database_path, database_url
        finally:
            cached = _database(database_url)
            cached[0].dispose()
            _database.cache_clear()
            database_path.unlink(missing_ok=True)
            Path(f"{database_path}-wal").unlink(missing_ok=True)
            Path(f"{database_path}-shm").unlink(missing_ok=True)
    assert not database_path.exists()
    if default_state is None:
        assert not default_database.exists()
    else:
        assert default_database.stat().st_mtime_ns == default_state


def login(client, email="candidate@example.com", password="candidate-password"):
    response = client.post(
        "/api/auth/login/", {"email": email, "password": password}, format="json"
    )
    assert response.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.json()['access_token']}")
    return client


def application_body(email, job_id="job-design"):
    return {
        "jobId": job_id,
        "candidateName": "Integration Candidate",
        "candidateEmail": email,
        "cvName": "integration.pdf",
        "coverLetter": "Interested in this role.",
    }


def test_sqlite_http_state_survives_new_request_sessions_and_is_isolated(sqlite_api):
    client, database_path, _database_url = sqlite_api

    # Migrations create a unique, empty database for this test; the first API
    # request seeds it, and it never points at developer local data.
    assert database_path.exists()
    assert client.get("/api/jobs/").status_code == 200
    assert database_path.exists()
    assert ".local-data" not in str(database_path)

    candidate = login(client)
    before = candidate.get("/api/saved-jobs/")
    assert before.status_code == 200
    assert before.json() == []

    saved = candidate.post(
        "/api/saved-jobs/", {"jobId": "job-platform"}, format="json"
    )
    assert saved.status_code == 204

    # Each request gets a new SQLAlchemy session; the next HTTP request reads
    # the committed state from the temporary SQLite file.
    assert candidate.get("/api/saved-jobs/").json()[0]["id"] == "job-platform"


def test_registration_without_email_and_disabled_recovery_persist_across_sqlite_request_sessions(sqlite_api):
    client, _database_path, _database_url = sqlite_api
    created = client.post("/api/auth/register/", {
        "name": "Persistent Candidate", "email": "persistent@example.com",
        "password": "persistent-password", "role": "candidate",
    }, format="json")
    assert created.status_code == 201
    assert created.json()["user"]["emailVerified"] is True
    assert client.post("/api/auth/login/", {
        "email": "persistent@example.com", "password": "persistent-password",
    }, format="json").status_code == 200
    for path in ("/api/auth/verify-email/", "/api/auth/password-reset/"):
        assert client.post(path, {}, format="json").status_code == 410


def test_sqlite_http_fixtures_start_clean_and_duplicate_applications_do_not_write_twice(sqlite_api):
    client, _database_path, _database_url = sqlite_api
    assert client.get("/api/jobs/").status_code == 200

    candidate = login(client)
    guest = APIClient()
    assert candidate.get("/api/saved-jobs/").json() == []

    registered = candidate.post(
        "/api/applications/", application_body("candidate@example.com"), format="json"
    )
    assert registered.status_code == 201
    duplicate_registered = candidate.post(
        "/api/applications/", application_body("candidate@example.com"), format="json"
    )
    assert duplicate_registered.status_code == 409
    assert sum(
        application["jobId"] == "job-design"
        for application in candidate.get("/api/candidate/applications/").json()
    ) == 1

    guest_body = application_body("guest-sqlite@example.com", job_id="job-platform")
    assert guest.post("/api/applications/guest/", guest_body, format="json").status_code == 201
    assert guest.post("/api/applications/guest/", guest_body, format="json").status_code == 409
    _engine, session_factory = _database(_database_url)
    with session_factory() as session:
        guest_application_count = session.scalar(
            select(func.count()).select_from(ApplicationRecord).where(
                ApplicationRecord.candidate_email == "guest-sqlite@example.com"
            )
        )
    assert guest_application_count == 1
    # A failed duplicate request leaves the application list unchanged and a
    # later successful read still works.
    assert guest.get("/api/jobs/").status_code == 200


def test_sqlite_foreign_key_failure_rolls_back_and_later_http_request_works(sqlite_api):
    client, _database_path, database_url = sqlite_api
    assert client.get("/api/jobs/").status_code == 200

    engine, session_factory = _database(database_url)
    try:
        with session_factory() as session:
            repository = Repository(session, JobRecord)
            with pytest.raises(IntegrityError):
                repository.save(
                    JobRecord(id="invalid-company-job", company_id="missing-company", title="Invalid")
                )
                session.flush()
            session.rollback()

        assert client.get("/api/jobs/").status_code == 200
        assert all(
            job["id"] != "invalid-company-job" for job in client.get("/api/jobs/").json()
        )
    finally:
        engine.dispose()


def test_sqlite_http_lifecycle_ownership_and_role_failures(sqlite_api):
    client, _database_path, database_url = sqlite_api
    assert client.get("/api/jobs/").status_code == 200

    anonymous = APIClient()
    assert anonymous.get("/api/candidate/profile/").status_code == 401
    candidate = login(client)
    assert candidate.get("/api/employer/dashboard/").status_code == 403
    own_withdrawal = candidate.post(
        "/api/applications/application-1/withdraw/", format="json"
    )
    assert own_withdrawal.status_code == 200
    assert own_withdrawal.json()["status"] == "Withdrawn"

    recruiter = login(APIClient(), "recruiter@example.com", "recruiter-password")
    assert recruiter.post(
        "/api/applications/application-1/withdraw/", format="json"
    ).status_code == 403
    assert recruiter.patch(
        "/api/employer/jobs/job-design/", {"title": "Wrong company"}, format="json"
    ).status_code == 404
    assert candidate.post(
        "/api/employer/applications/application-1/status/",
        {"status": "Rejected"},
        format="json",
    ).status_code == 403

    deadline = (timezone.now() + timezone.timedelta(days=2)).isoformat()
    created = recruiter.post(
        "/api/employer/jobs/",
        {
            "title": "SQLite lifecycle role",
            "description": "Integration role",
            "location": "Remote",
            "deadline": deadline,
        },
        format="json",
    )
    assert created.status_code == 201
    job_id = created.json()["id"]
    assert recruiter.post(
        f"/api/employer/jobs/{job_id}/status/", {"status": "Published"}, format="json"
    ).status_code == 200
    assert recruiter.post(
        f"/api/employer/jobs/{job_id}/status/", {"status": "Closed"}, format="json"
    ).status_code == 200
    rejected_application = candidate.post(
        "/api/applications/",
        application_body("candidate@example.com", job_id=job_id),
        format="json",
    )
    assert rejected_application.status_code == 400

    expired = recruiter.post(
        "/api/employer/jobs/",
        {
            "title": "SQLite expired role",
            "description": "Expired integration role",
            "location": "Remote",
            "deadline": deadline,
        },
        format="json",
    )
    assert expired.status_code == 201
    expired_id = expired.json()["id"]
    assert recruiter.post(
        f"/api/employer/jobs/{expired_id}/status/", {"status": "Published"}, format="json"
    ).status_code == 200
    past_deadline = (timezone.now() - timezone.timedelta(days=1)).isoformat()
    assert recruiter.patch(
        f"/api/employer/jobs/{expired_id}/", {"deadline": past_deadline}, format="json"
    ).status_code == 400

    # Simulate time passing after publication; API writes correctly reject
    # past deadlines, so move the stored deadline to exercise expiration.
    _engine, session_factory = _database(database_url)
    with session_factory() as session:
        session.get(JobRecord, expired_id).deadline = timezone.now() - timezone.timedelta(days=1)
        session.commit()
    assert recruiter.post(
        f"/api/employer/jobs/{expired_id}/status/", {"status": "Expired"}, format="json"
    ).status_code == 200
    expired_application = candidate.post(
        "/api/applications/",
        application_body("candidate@example.com", job_id=expired_id),
        format="json",
    )
    assert expired_application.status_code == 400


def test_sqlite_failure_does_not_leave_partial_application_or_break_session(sqlite_api):
    from sqlalchemy import event

    client, _database_path, database_url = sqlite_api
    assert client.get("/api/jobs/").status_code == 200
    engine, _ = _database(database_url)
    checked_in = []
    event.listen(engine, "checkin", lambda *_: checked_in.append(True))
    candidate = login(client)

    invalid = candidate.post(
        "/api/applications/", application_body("candidate@example.com", "missing-job"), format="json"
    )
    assert invalid.status_code == 404
    after_error_checkins = len(checked_in)
    assert after_error_checkins >= 1
    applications = candidate.get("/api/candidate/applications/")
    assert applications.status_code == 200
    assert [application["id"] for application in applications.json()] == ["application-1"]
    assert len(checked_in) > after_error_checkins
    assert candidate.get("/api/jobs/").status_code == 200
