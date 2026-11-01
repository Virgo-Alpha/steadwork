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


def test_non_member_cannot_use_employer_api():
    candidate = logged_in("candidate@example.com", "candidate-password")
    assert candidate.get("/api/employer/dashboard/").status_code == 403
    assert candidate.get("/api/employer/jobs/").status_code == 403
