import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from api.store import get_store, reset_store


@pytest.fixture(autouse=True)
def clean_store():
    reset_store()
    yield
    reset_store()


def logged_in(email="recruiter@example.com", password="recruiter-password"):
    client = APIClient()
    response = client.post("/api/auth/login/", {"email": email, "password": password}, format="json")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.json()['access_token']}")
    return client


def test_employer_dashboard_and_job_ownership():
    client = logged_in()
    dashboard = client.get("/api/employer/dashboard/")
    assert dashboard.status_code == 200
    assert dashboard.json()["totalJobs"] == 1
    assert dashboard.json()["activeJobs"] == 1
    assert dashboard.json()["applications"] == 1
    assert len(client.get("/api/employer/jobs/").json()) == 1
    assert client.patch("/api/employer/jobs/job-design/", {"title": "Nope"}, format="json").status_code == 404


def test_job_lifecycle_requires_fields_and_deadline():
    client = logged_in()
    created = client.post("/api/employer/jobs/", {"title": "New role", "description": "Work"}, format="json")
    assert created.status_code == 201 and created.json()["status"] == "Draft"
    job_id = created.json()["id"]
    assert client.post(f"/api/employer/jobs/{job_id}/status/", {"status": "Published"}, format="json").status_code == 400
    assert client.patch(f"/api/employer/jobs/{job_id}/", {
        "deadline": (timezone.now() + timezone.timedelta(days=2)).isoformat(),
        "location": "Remote",
    }, format="json").status_code == 200
    assert client.post(f"/api/employer/jobs/{job_id}/status/", {"status": "Published"}, format="json").status_code == 200
    assert client.post(f"/api/employer/jobs/{job_id}/status/", {"status": "Draft"}, format="json").status_code == 400


def test_job_deadline_must_be_today_or_future():
    client = logged_in()
    today = timezone.now().date()
    yesterday = today - timezone.timedelta(days=1)
    tomorrow = today + timezone.timedelta(days=1)
    past = client.post("/api/employer/jobs/", {
        "title": "Past deadline", "deadline": yesterday.isoformat(),
    }, format="json")
    assert past.status_code == 400

    current_day = client.post("/api/employer/jobs/", {
        "title": "Today deadline", "description": "Work", "location": "Remote",
        "deadline": today.isoformat(),
    }, format="json")
    assert current_day.status_code == 201
    current_day_id = current_day.json()["id"]
    assert client.post(f"/api/employer/jobs/{current_day_id}/status/", {"status": "Published"}, format="json").status_code == 200

    future = client.post("/api/employer/jobs/", {
        "title": "Future deadline", "deadline": tomorrow.isoformat(),
    }, format="json")
    assert future.status_code == 201
    assert client.patch(f"/api/employer/jobs/{future.json()['id']}/", {
        "deadline": yesterday.isoformat(),
    }, format="json").status_code == 400


def test_job_write_rejects_response_only_fields():
    client = logged_in()
    response = client.post("/api/employer/jobs/", {
        "title": "New role", "description": "Work", "location": "Remote",
        "status": "Draft",
    }, format="json")
    assert response.status_code == 400


def test_published_close_and_expire_require_correct_deadline_rules():
    client = logged_in()
    future = (timezone.now() + timezone.timedelta(days=2)).isoformat()
    created = client.post("/api/employer/jobs/", {
        "title": "Closable role", "description": "Work", "location": "Remote", "deadline": future,
    }, format="json")
    job_id = created.json()["id"]
    assert client.post(f"/api/employer/jobs/{job_id}/status/", {"status": "Published"}, format="json").status_code == 200
    assert client.post(f"/api/employer/jobs/{job_id}/status/", {"status": "Closed"}, format="json").status_code == 200

    expired = client.post("/api/employer/jobs/", {
        "title": "Expiring role", "description": "Work", "location": "Remote",
        "deadline": (timezone.now() + timezone.timedelta(days=2)).isoformat(),
    }, format="json")
    expired_id = expired.json()["id"]
    store_job = next(job for job in get_store().jobs if job.id == expired_id)
    store_job.deadline = timezone.now() - timezone.timedelta(days=1)
    assert client.post(f"/api/employer/jobs/{expired_id}/status/", {"status": "Published"}, format="json").status_code == 400
    store_job.status = "Published"
    assert client.post(f"/api/employer/jobs/{expired_id}/status/", {"status": "Expired"}, format="json").status_code == 200


def test_republishing_requires_required_job_fields():
    client = logged_in()
    job = client.post("/api/employer/jobs/", {
        "title": "Republishable role", "description": "Work", "location": "Remote",
        "deadline": (timezone.now() + timezone.timedelta(days=2)).isoformat(),
    }).json()
    job_id = job["id"]
    assert client.post(f"/api/employer/jobs/{job_id}/status/", {"status": "Published"}).status_code == 200
    assert client.patch(f"/api/employer/jobs/{job_id}/", {
        "title": "", "description": "", "location": "",
    }).status_code == 200
    assert client.post(f"/api/employer/jobs/{job_id}/status/", {"status": "Closed"}).status_code == 200
    assert client.post(f"/api/employer/jobs/{job_id}/status/", {"status": "Published"}).status_code == 400


def test_application_status_and_notifications_are_scoped():
    recruiter = logged_in()
    candidate = logged_in("candidate@example.com", "candidate-password")
    response = candidate.post("/api/applications/", {
        "jobId": "job-platform", "candidateName": "Candidate",
        "candidateEmail": "candidate@example.com", "cvName": "cv.pdf", "coverLetter": "",
    }, format="json")
    assert response.status_code == 409  # seeded application
    app_id = get_store().applications[0].id
    updated = recruiter.post(f"/api/employer/applications/{app_id}/status/", {"status": "Under Review"}, format="json")
    assert updated.status_code == 200
    assert recruiter.post(f"/api/employer/applications/{app_id}/status/", {"status": "Hired"}, format="json").status_code == 400
    candidate_notifications = candidate.get("/api/notifications/")
    assert candidate_notifications.status_code == 200
    assert len(candidate_notifications.json()) == 1
    notification_id = candidate_notifications.json()[0]["id"]
    assert candidate.post(f"/api/notifications/{notification_id}/read/", format="json").status_code == 204
    assert candidate.post(f"/api/notifications/{notification_id}/read/", format="json").status_code == 204
    assert recruiter.post(f"/api/notifications/{notification_id}/read/", format="json").status_code == 404


def test_shortlisted_application_can_be_rejected():
    recruiter = logged_in()
    app_id = get_store().applications[0].id
    assert recruiter.post(f"/api/employer/applications/{app_id}/status/", {"status": "Under Review"}, format="json").status_code == 200
    assert recruiter.post(f"/api/employer/applications/{app_id}/status/", {"status": "Shortlisted"}, format="json").status_code == 200
    rejected = recruiter.post(f"/api/employer/applications/{app_id}/status/", {"status": "Rejected"}, format="json")
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "Rejected"


def test_non_member_cannot_use_employer_api():
    candidate = logged_in("candidate@example.com", "candidate-password")
    assert candidate.get("/api/employer/dashboard/").status_code == 403
    assert candidate.get("/api/employer/jobs/").status_code == 403
