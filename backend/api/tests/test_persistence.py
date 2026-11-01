"""Focused persistence tests for issue #14; SQLite stays isolated per test."""

from copy import deepcopy

import pytest
from django.conf import settings
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from rest_framework.test import APIClient

from api.database import DatabaseConfigurationError, get_database_url, get_store_backend
from api.models import Application, Company, Job, Membership, Notification, User
from api.orm import (
    ApplicationRecord,
    CompanyRecord,
    JobRecord,
    MembershipRecord,
    NotificationRecord,
    ProfileRecord,
    SavedJobRecord,
    UserRecord,
)
from api.repositories import Repository, SQLAlchemyStoreRepository
from api.store import _seed
from api.tests.migration_helpers import upgrade_database


def test_default_database_is_an_ignored_local_sqlite_file():
    url = get_database_url({})
    assert url.startswith("sqlite:///")
    assert url.endswith("/backend/.local-data/steadwork.sqlite3")
    assert settings.STORE_BACKEND == "inmemory"
    assert get_store_backend({}) == "sqlite"
    assert get_store_backend({"STEADWORK_STORE": "inmemory"}) == "inmemory"
    with pytest.raises(DatabaseConfigurationError, match="STEADWORK_STORE"):
        get_store_backend({"STEADWORK_STORE": "memory-ish"})


def test_database_url_override_and_invalid_backend():
    assert get_database_url({"DATABASE_URL": "sqlite:////tmp/steadwork-test.sqlite3"}) == "sqlite:////tmp/steadwork-test.sqlite3"
    assert get_database_url({"DATABASE_URL": "postgresql://user:pass@localhost/db"}) == "postgresql+psycopg://user:pass@localhost/db"
    with pytest.raises(DatabaseConfigurationError, match="SQLite or PostgreSQL"):
        get_database_url({"DATABASE_URL": "mysql://user:pass@localhost/db"})
    with pytest.raises(DatabaseConfigurationError, match="valid SQLAlchemy URL"):
        get_database_url({"DATABASE_URL": "not a url"})


def test_repository_crud_for_every_persisted_entity(tmp_path):
    from api.repositories import create_database

    database_url = f"sqlite:///{tmp_path / 'crud.sqlite3'}"
    upgrade_database(database_url)
    engine, factory = create_database(database_url)
    with factory() as session:
        repositories = {
            model: Repository(session, model)
            for model in (
                UserRecord, CompanyRecord, JobRecord, ApplicationRecord,
                ProfileRecord, SavedJobRecord, MembershipRecord, NotificationRecord,
            )
        }
        records = [
            UserRecord(id="u", email="u@example.com", role="candidate", password_hash="hash"),
            CompanyRecord(id="c", name="Company"),
            JobRecord(id="j", company_id="c", title="Role"),
            ApplicationRecord(id="a", job_id="j", candidate_id="u", status="Applied"),
            ProfileRecord(user_id="u", data={"userId": "u", "skills": ["Python"]}),
            SavedJobRecord(user_id="u", job_id="j"),
            MembershipRecord(user_id="u", company_id="c", role="admin"),
            NotificationRecord(id="n", user_id="u", title="Title", body="Body"),
        ]
        for record in records:
            repository = repositories[type(record)]
            repository.save(record)
            session.flush()
            key = getattr(record, "id", None) or tuple(
                getattr(record, name) for name in repository.primary_key_names
            )
            assert repository.get(key) is not None
            assert repository.list()
            if isinstance(record, UserRecord):
                record.email = "updated@example.com"
            elif isinstance(record, CompanyRecord):
                record.name = "Updated company"
            elif isinstance(record, JobRecord):
                record.title = "Updated"
            elif isinstance(record, ApplicationRecord):
                record.status = "Under Review"
            elif isinstance(record, ProfileRecord):
                record.data = {"userId": "u", "skills": ["Updated"]}
            elif isinstance(record, MembershipRecord):
                record.role = "recruiter"
            elif isinstance(record, NotificationRecord):
                record.title = "Updated notification"
            repository.save(record)
            session.flush()
            assert repository.get(key) is not None
        session.commit()

        assert repositories[JobRecord].get("j").company.name == "Updated company"
        assert repositories[ApplicationRecord].get("a").job.title == "Updated"

        replacement = SavedJobRecord(user_id="u", job_id="j")
        repositories[SavedJobRecord].delete(("u", "j"))
        repositories[SavedJobRecord].save(replacement)
        session.flush()

        with pytest.raises(IntegrityError):
            session.add(UserRecord(id="duplicate-email", email="updated@example.com", role="candidate", password_hash="hash"))
            session.flush()
        session.rollback()
        with pytest.raises(IntegrityError):
            session.add(SavedJobRecord(user_id="u", job_id="j"))
            session.flush()
        session.rollback()

        unattached = CompanyRecord(id="delete-me", name="Temporary")
        repositories[CompanyRecord].save(unattached)
        session.flush()
        repositories[CompanyRecord].delete("delete-me")
        session.flush()
        assert repositories[CompanyRecord].get("delete-me") is None

        with pytest.raises(IntegrityError):
            repositories[CompanyRecord].delete("c")
            session.flush()
        session.rollback()
        with pytest.raises(IntegrityError):
            repositories[JobRecord].save(JobRecord(id="orphan", company_id="missing", title="Orphan"))
            session.flush()
        session.rollback()

        for model, key in (
            (NotificationRecord, "n"), (SavedJobRecord, ("u", "j")),
            (MembershipRecord, ("u", "c")), (ProfileRecord, "u"),
            (ApplicationRecord, "a"), (JobRecord, "j"),
            (CompanyRecord, "c"), (UserRecord, "u"),
        ):
            assert repositories[model].delete(key)
            session.flush()
            assert repositories[model].get(key) is None
    engine.dispose()


def test_store_repository_round_trips_all_domain_data_and_updates(tmp_path):
    from api.repositories import create_database

    database_url = f"sqlite:///{tmp_path / 'store.sqlite3'}"
    upgrade_database(database_url)
    engine, factory = create_database(database_url)
    with factory() as session:
        repository = SQLAlchemyStoreRepository(session)
        repository.replace(_seed())
        session.commit()
    with factory() as session:
        repository = SQLAlchemyStoreRepository(session)
        restored = repository.load()
        assert [item.id for item in restored.users] == ["user-candidate", "user-recruiter", "user-admin"]
        assert [item.id for item in restored.companies] == ["company-acme", "company-orbit"]
        assert [item.id for item in restored.jobs] == ["job-platform", "job-design"]
        assert [item.id for item in restored.applications] == ["application-1"]
        assert restored.memberships and restored.profiles == {} and restored.saved_jobs == {}
        assert restored.notifications == []

        restored.jobs[0].title = "Persisted after update"
        restored.profiles["user-candidate"] = {"userId": "user-candidate", "skills": ["SQL"]}
        restored.saved_jobs["user-candidate"] = {"job-platform"}
        restored.notifications.append(Notification("n1", "user-candidate", "Update", "Body"))
        restored.applications.append(Application("a2", "job-platform", "user-candidate", "Applied"))
        repository.replace(restored)
        session.commit()
    with factory() as session:
        restored = SQLAlchemyStoreRepository(session).load()
        assert restored.jobs[0].title == "Persisted after update"
        assert restored.profiles["user-candidate"]["skills"] == ["SQL"]
        assert restored.saved_jobs["user-candidate"] == {"job-platform"}
        assert restored.notifications[0].id == "n1"
        assert {application.id for application in restored.applications} == {"application-1", "a2"}
    engine.dispose()


def test_stale_request_diff_cannot_erase_a_newer_committed_mutation(tmp_path):
    from api.repositories import create_database

    database_url = f"sqlite:///{tmp_path / 'stale-request.sqlite3'}"
    upgrade_database(database_url)
    engine, factory = create_database(database_url)
    with factory() as session:
        repository = SQLAlchemyStoreRepository(session)
        initial = repository.load()
        session.commit()

    # Request B hydrates an older snapshot, then pauses before its route writes.
    with factory() as session_b:
        stale = deepcopy(SQLAlchemyStoreRepository(session_b).load())

    # Request A commits a saved-job mutation after B's snapshot was taken.
    with factory() as session_a:
        repository_a = SQLAlchemyStoreRepository(session_a)
        current = repository_a.load()
        before_a = deepcopy(current)
        current.saved_jobs["user-candidate"] = {"job-design"}
        repository_a.apply_changes(before_a, current)
        session_a.commit()

    # B then commits an unrelated notification from its old snapshot. A full
    # snapshot replacement would drop A's saved job; the row diff cannot.
    stale.notifications.append(Notification("stale-note", "user-candidate", "Saved job", "Body"))
    with factory() as session_b:
        SQLAlchemyStoreRepository(session_b).apply_changes(initial, stale)
        session_b.commit()

    with factory() as session:
        final = SQLAlchemyStoreRepository(session).load()
        assert final.saved_jobs["user-candidate"] == {"job-design"}
        assert [item.id for item in final.notifications] == ["stale-note"]
    engine.dispose()


def test_sqlite_requests_keep_api_behavior_and_close_sessions_after_errors(tmp_path):
    from django.test import override_settings
    from api.middleware import _database

    database_url = f"sqlite:///{tmp_path / 'api.sqlite3'}"
    upgrade_database(database_url)
    _database.cache_clear()
    try:
        with override_settings(STORE_BACKEND="sqlite", DATABASE_URL=database_url):
            client = APIClient()
            anonymous = APIClient()
            assert anonymous.get("/api/employer/dashboard/").status_code == 401
            assert client.get("/api/companies/").status_code == 200
            assert client.get("/api/companies/company-acme/").json()["id"] == "company-acme"
            health = client.get("/api/health/")
            assert health.status_code == 200
            assert health.json()["store"] == "sqlite"
            engine, _ = _database(database_url)
            writes = []
            event.listen(
                engine,
                "before_cursor_execute",
                lambda _connection, _cursor, statement, *_: writes.append(statement)
                if statement.lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE")) else None,
            )
            assert client.get("/api/jobs/").status_code == 200
            assert writes == []
            assert anonymous.get("/api/protected/candidate/").status_code == 401
            assert client.get("/api/candidate/profile/").status_code == 401
            login = client.post(
                "/api/auth/login/",
                {"email": "candidate@example.com", "password": "candidate-password"},
                format="json",
            )
            assert login.status_code == 200
            client.credentials(HTTP_AUTHORIZATION="Bearer " + login.json()["access_token"])
            assert client.get("/api/auth/me/").json()["id"] == "user-candidate"
            assert client.get("/api/employer/dashboard/").status_code == 403
            assert client.get("/api/jobs/job-platform/").status_code == 200
            saved = client.post("/api/saved-jobs/", {"jobId": "job-platform"}, format="json")
            assert saved.status_code == 204
            listed = client.get("/api/saved-jobs/")
            assert listed.status_code == 200
            assert [job["id"] for job in listed.json()] == ["job-platform"]
            assert client.delete("/api/saved-jobs/job-platform/").status_code == 204
            assert client.post("/api/saved-jobs/", {"jobId": "job-platform"}, format="json").status_code == 204
            assert client.get("/api/candidate/applications/").json()[0]["id"] == "application-1"

            registered_application = client.post(
                "/api/applications/",
                {"jobId": "job-design", "candidateName": "Candidate", "candidateEmail": "candidate@example.com", "cvName": "candidate.pdf", "coverLetter": "Interested"},
                format="json",
            )
            assert registered_application.status_code == 201
            assert registered_application.json()["status"] == "External click"
            guest_application = client.post(
                "/api/applications/guest/",
                {"jobId": "job-platform", "candidateName": "Guest", "candidateEmail": "guest@example.com", "cvName": "guest.pdf", "coverLetter": ""},
                format="json",
            )
            assert guest_application.status_code == 201
            profile = client.patch("/api/candidate/profile/", {"headline": "Persistent engineer"}, format="json")
            assert profile.status_code == 200
            assert profile.json()["headline"] == "Persistent engineer"

            employer = APIClient()
            recruiter_login = employer.post(
                "/api/auth/login/",
                {"email": "recruiter@example.com", "password": "recruiter-password"},
                format="json",
            )
            assert recruiter_login.status_code == 200
            employer.credentials(HTTP_AUTHORIZATION="Bearer " + recruiter_login.json()["access_token"])
            dashboard = employer.get("/api/employer/dashboard/")
            assert dashboard.status_code == 200
            assert employer.get("/api/employer/jobs/").status_code == 200
            applicants = employer.get("/api/employer/jobs/job-platform/applications/")
            assert applicants.status_code == 200
            assert applicants.json()[0]["id"] == "application-1"
            changed = employer.post(
                "/api/employer/applications/application-1/status/",
                {"status": "Under Review"},
                format="json",
            )
            assert changed.status_code == 200
            assert changed.json()["status"] == "Under Review"
            assert client.post(f"/api/applications/{changed.json()['id']}/withdraw/").json()["status"] == "Withdrawn"
            notes = client.get("/api/notifications/")
            assert notes.status_code == 200
            assert notes.json()[0]["title"] == "Application status updated"
            read = client.post(f"/api/notifications/{notes.json()[0]['id']}/read/")
            assert read.status_code == 204

            created_job = employer.post("/api/employer/jobs/", {
                "title": "New platform role", "description": "Build systems", "location": "Remote",
                "salaryMin": 1, "salaryMax": 2, "currency": "USD", "remotePolicy": "Remote",
                "jobType": "Full-time", "experienceLevel": "Mid", "skills": [], "responsibilities": [],
                "qualifications": [], "benefits": [], "applicationMethod": "Internal",
                "deadline": "2099-01-01T00:00:00Z",
            }, format="json")
            assert created_job.status_code == 201
            job_id = created_job.json()["id"]
            assert employer.patch(f"/api/employer/jobs/{job_id}/", {"title": "Updated platform role"}, format="json").status_code == 200
            assert employer.post(f"/api/employer/jobs/{job_id}/status/", {"status": "Published"}, format="json").status_code == 200
            assert employer.post(f"/api/employer/jobs/{job_id}/status/", {"status": "Closed"}, format="json").status_code == 200
            assert employer.get(f"/api/employer/jobs/{job_id}/applications/").json() == []

            engine, _ = _database(database_url)
            connection_checkins = []
            event.listen(engine, "checkin", lambda *_: connection_checkins.append(True))
            bad_request = client.get("/api/jobs/?sort=invalid")
            assert bad_request.status_code == 400
            assert connection_checkins
            checkins_after_error = len(connection_checkins)
            healthy_after_error = client.get("/api/jobs/")
            assert healthy_after_error.status_code == 200
            assert healthy_after_error.json()
            assert len(connection_checkins) > checkins_after_error

            # Drop the process engine cache, then prove mutations survive a
            # fresh engine and are not replaced with startup seed defaults.
            engine, _ = _database(database_url)
            engine.dispose()
            _database.cache_clear()
            restarted_client = APIClient()
            restarted_login = restarted_client.post(
                "/api/auth/login/",
                {"email": "candidate@example.com", "password": "candidate-password"},
                format="json",
            )
            restarted_client.credentials(HTTP_AUTHORIZATION="Bearer " + restarted_login.json()["access_token"])
            restarted_saved = restarted_client.get("/api/saved-jobs/")
            assert restarted_saved.status_code == 200
            assert [job["id"] for job in restarted_saved.json()] == ["job-platform"]
            assert restarted_client.get("/api/candidate/profile/").json()["headline"] == "Persistent engineer"
            assert any(app["status"] == "Withdrawn" for app in restarted_client.get("/api/candidate/applications/").json())
            assert restarted_client.get("/api/notifications/").json()[0].get("readAt")

            restarted_employer = APIClient()
            restarted_recruiter = restarted_employer.post(
                "/api/auth/login/",
                {"email": "recruiter@example.com", "password": "recruiter-password"},
                format="json",
            )
            restarted_employer.credentials(HTTP_AUTHORIZATION="Bearer " + restarted_recruiter.json()["access_token"])
            restarted_jobs = restarted_employer.get("/api/employer/jobs/").json()
            persisted_job = next(job for job in restarted_jobs if job["title"] == "Updated platform role")
            assert persisted_job["status"] == "Closed"
            persisted_apps = restarted_employer.get("/api/employer/jobs/job-platform/applications/").json()
            assert next(app for app in persisted_apps if app["id"] == "application-1")["status"] == "Withdrawn"
    finally:
        _database.cache_clear()
