import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from api.store import get_store, reset_store


@pytest.fixture(autouse=True)
def clean_store():
    reset_store()
    yield
    reset_store()


def client():
    c = APIClient()
    login = c.post("/api/auth/login/", {"email": "candidate@example.com", "password": "candidate-password"}, format="json")
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access_token']}")
    return c


def test_profile_saved_jobs_and_application_listing_are_scoped():
    c = client()
    profile = c.get("/api/candidate/profile/")
    assert profile.status_code == 200 and profile.json()["userId"] == "user-candidate"
    assert c.patch("/api/candidate/profile/", {"headline": "Engineer", "skills": ["Python"]}, format="json").json()["headline"] == "Engineer"
    assert c.post("/api/saved-jobs/", {"jobId": "job-platform"}, format="json").status_code == 204
    assert c.post("/api/saved-jobs/", {"jobId": "job-platform"}, format="json").status_code == 204
    assert [j["id"] for j in c.get("/api/saved-jobs/").json()] == ["job-platform"]
    assert c.delete("/api/saved-jobs/job-platform/").status_code == 204
    assert all(a["candidateId"] == "user-candidate" for a in c.get("/api/candidate/applications/").json())


def test_registered_and_guest_applications_validate_duplicates_and_lifecycle():
    c = client()
    get_store().applications.clear()
    body = {"jobId": "job-platform", "candidateName": "Candidate", "candidateEmail": "candidate@example.com", "cvName": "cv.pdf", "coverLetter": ""}
    created = c.post("/api/applications/", body, format="json")
    assert created.status_code == 201 and created.json()["status"] == "Applied"
    assert c.post("/api/applications/", body, format="json").status_code == 409
    assert c.post("/api/applications/guest/", {**body, "candidateEmail": " Guest@Example.com "}, format="json").status_code == 201
    assert c.post("/api/applications/guest/", {**body, "candidateEmail": "guest@example.com"}, format="json").status_code == 409
    withdrawn = c.post(f"/api/applications/{created.json()['id']}/withdraw/", format="json")
    assert withdrawn.status_code == 200 and withdrawn.json()["status"] == "Withdrawn"
    assert c.post(f"/api/applications/{created.json()['id']}/withdraw/", format="json").status_code == 400
    assert c.post("/api/applications/", body, format="json").status_code == 409


def test_application_rejects_wrong_role_invalid_fields_and_unavailable_jobs():
    c = client()
    assert c.post("/api/applications/", {"jobId": "job-platform"}, format="json").status_code == 400
    job = get_store().jobs[0]
    job.application_method = "External"
    assert c.post("/api/applications/", {"jobId": job.id, "candidateName": "x", "candidateEmail": "candidate@example.com", "cvName": "x", "coverLetter": ""}, format="json").status_code == 400
    recruiter = APIClient()
    login = recruiter.post("/api/auth/login/", {"email": "recruiter@example.com", "password": "recruiter-password"}, format="json")
    recruiter.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access_token']}")
    assert recruiter.get("/api/candidate/profile/").status_code == 403
