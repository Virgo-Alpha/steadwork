import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from api.store import reset_store


@pytest.fixture(autouse=True)
def isolated_store():
    reset_store()
    yield
    reset_store()


def authenticated(email, password):
    client = APIClient()
    response = client.post(
        "/api/auth/login/", {"email": email, "password": password}, format="json"
    )
    assert response.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.json()['access_token']}")
    return client


def test_authenticated_me_returns_current_user():
    client = APIClient()
    login = client.post(
        "/api/auth/login/",
        {"email": "candidate@example.com", "password": "candidate-password"},
        format="json",
    )
    token = login.json()["access_token"]
    response = client.get("/api/auth/me/", HTTP_AUTHORIZATION=f"Bearer {token}")
    assert response.status_code == 200
    assert response.json() == login.json()["user"]


def test_me_requires_bearer_authentication():
    assert APIClient().get("/api/auth/me/").status_code == 401


def application_body(email="candidate@example.com", job_id="job-platform"):
    return {
        "jobId": job_id,
        "candidateName": "Candidate",
        "candidateEmail": email,
        "cvName": "candidate.pdf",
        "coverLetter": "",
    }


def test_public_health_jobs_companies_and_missing_resources():
    client = APIClient()

    health = client.get("/api/health/")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["store"] == "in-memory"
    assert health.json()["authenticated"] is False

    jobs = client.get("/api/jobs/")
    assert jobs.status_code == 200
    assert {"job-platform", "job-design", "job-security", "job-analytics", "job-infrastructure", "job-research", "job-devrel", "job-accessibility"} <= {job["id"] for job in jobs.json()}
    assert all(job["status"] == "Published" for job in jobs.json())
    assert {"companyId", "salaryMin", "responsibilities"} <= jobs.json()[0].keys()
    assert client.get("/api/jobs/job-platform/").json()["title"] == "Platform Engineer"

    companies = client.get("/api/companies/")
    assert companies.status_code == 200
    assert companies.json()[0]["id"] == "company-acme"
    assert client.get("/api/companies/company-acme/").json()["name"] == "Acme Technologies"
    assert client.get("/api/jobs/missing/").status_code == 404
    assert client.get("/api/companies/missing/").status_code == 404


def test_authentication_and_bearer_role_and_ownership_failures():
    public = APIClient()
    invalid = public.post(
        "/api/auth/login/",
        {"email": "candidate@example.com", "password": "wrong"},
        format="json",
    )
    assert invalid.status_code == 401
    assert "detail" in invalid.json()

    candidate = authenticated("candidate@example.com", "candidate-password")
    assert candidate.get("/api/protected/candidate/").json()["role"] == "candidate"
    assert candidate.get("/api/protected/candidate/user-candidate/").status_code == 200
    assert candidate.get("/api/protected/candidate/user-recruiter/").status_code == 403
    assert candidate.get("/api/protected/recruiter/").status_code == 403
    assert candidate.get("/api/protected/admin/").status_code == 403

    missing = APIClient()
    assert missing.get("/api/protected/candidate/").status_code == 401
    missing.credentials(HTTP_AUTHORIZATION="Bearer not-a-token")
    assert missing.get("/api/protected/candidate/").status_code == 401

    recruiter = authenticated("recruiter@example.com", "recruiter-password")
    assert recruiter.get("/api/protected/recruiter/user-recruiter/").status_code == 200
    assert recruiter.get("/api/protected/candidate/").status_code == 403


def test_candidate_profile_saved_jobs_and_application_withdrawal():
    client = authenticated("candidate@example.com", "candidate-password")

    profile = client.get("/api/candidate/profile/")
    assert profile.status_code == 200
    assert profile.json()["userId"] == "user-candidate"
    updated = client.patch(
        "/api/candidate/profile/",
        {"headline": "Platform engineer", "skills": ["Python"]},
        format="json",
    )
    assert updated.status_code == 200
    assert updated.json()["headline"] == "Platform engineer"
    assert client.patch("/api/candidate/profile/", {"skills": "Python"}, format="json").status_code == 400
    assert client.patch("/api/candidate/profile/", {"userId": "user-recruiter"}, format="json").status_code == 403

    assert client.post("/api/saved-jobs/", {"jobId": "job-platform"}, format="json").status_code == 204
    assert client.post("/api/saved-jobs/", {"jobId": "job-platform"}, format="json").status_code == 204
    assert [job["id"] for job in client.get("/api/saved-jobs/").json()] == ["job-platform"]
    assert client.delete("/api/saved-jobs/job-platform/").status_code == 204
    assert client.delete("/api/saved-jobs/job-platform/").status_code == 404
    assert client.post("/api/saved-jobs/", {"jobId": "missing"}, format="json").status_code == 404

    employer = authenticated("recruiter@example.com", "recruiter-password")
    new_job = employer.post(
        "/api/employer/jobs/",
        {
            "title": "Internal role",
            "description": "Work",
            "location": "Remote",
            "deadline": (timezone.now() + timezone.timedelta(days=2)).isoformat(),
        },
        format="json",
    )
    assert new_job.status_code == 201
    job_id = new_job.json()["id"]
    assert employer.post(
        f"/api/employer/jobs/{job_id}/status/", {"status": "Published"}, format="json"
    ).status_code == 200

    created = client.post(
        "/api/applications/", application_body("candidate@example.com", job_id), format="json"
    )
    assert created.status_code == 201
    assert created.json()["status"] == "Applied"
    assert created.json()["jobId"] == job_id
    application_id = created.json()["id"]
    assert client.get("/api/candidate/applications/").json()[0]["candidateId"] == "user-candidate"
    withdrawn = client.post(f"/api/applications/{application_id}/withdraw/", format="json")
    assert withdrawn.status_code == 200
    assert withdrawn.json()["status"] == "Withdrawn"
    assert client.post(f"/api/applications/{application_id}/withdraw/", format="json").status_code == 400
    assert client.post("/api/applications/", {"jobId": "job-platform"}, format="json").status_code == 400


def test_guest_application_normalizes_duplicates_and_rejects_closed_or_invalid_input():
    client = APIClient()
    body = application_body(" Guest@Example.com ")
    created = client.post("/api/applications/guest/", body, format="json")
    assert created.status_code == 201
    assert created.json()["status"] == "Applied"
    assert created.json()["candidateEmail"] == "guest@example.com"
    assert client.post("/api/applications/guest/", application_body("guest@example.com"), format="json").status_code == 409
    assert client.post(
        "/api/applications/guest/", {**application_body("other@example.com"), "candidateEmail": "bad"}, format="json"
    ).status_code == 400
    assert client.post(
        "/api/applications/guest/", application_body("other@example.com", "missing"), format="json"
    ).status_code == 404

    closed = client.post(
        "/api/applications/guest/", application_body("closed@example.com", "job-design"), format="json"
    )
    assert closed.status_code == 201
    # A second request demonstrates duplicate handling for an externally applied job too.
    assert client.post(
        "/api/applications/guest/", application_body("closed@example.com", "job-design"), format="json"
    ).status_code == 409


def test_employer_dashboard_job_lifecycle_and_ownership():
    client = authenticated("recruiter@example.com", "recruiter-password")
    dashboard = client.get("/api/employer/dashboard/")
    assert dashboard.status_code == 200
    assert dashboard.json()["totalJobs"] == 1
    assert dashboard.json()["activeJobs"] == 1
    assert dashboard.json()["applications"] == 1
    assert len(client.get("/api/employer/jobs/").json()) == 1
    assert client.patch("/api/employer/jobs/job-design/", {"title": "Nope"}, format="json").status_code == 404

    created = client.post("/api/employer/jobs/", {"title": "New role", "description": "Work"}, format="json")
    assert created.status_code == 201
    assert created.json()["status"] == "Draft"
    job_id = created.json()["id"]
    assert client.post(f"/api/employer/jobs/{job_id}/status/", {"status": "Published"}, format="json").status_code == 400
    deadline = (timezone.now() + timezone.timedelta(days=2)).isoformat()
    patched = client.patch(
        f"/api/employer/jobs/{job_id}/",
        {"deadline": deadline, "location": "Remote"},
        format="json",
    )
    assert patched.status_code == 200
    assert client.post(f"/api/employer/jobs/{job_id}/status/", {"status": "Published"}, format="json").status_code == 200
    assert client.post(f"/api/employer/jobs/{job_id}/status/", {"status": "Draft"}, format="json").status_code == 400
    assert client.get(f"/api/employer/jobs/{job_id}/applications/").status_code == 200
    assert client.get("/api/employer/jobs/missing/applications/").status_code == 404

    candidate = authenticated("candidate@example.com", "candidate-password")
    assert candidate.get("/api/employer/dashboard/").status_code == 403
    assert candidate.get("/api/employer/jobs/").status_code == 403


def test_employer_application_status_notifications_and_cross_user_denial():
    recruiter = authenticated("recruiter@example.com", "recruiter-password")
    candidate = authenticated("candidate@example.com", "candidate-password")
    application_id = "application-1"

    updated = recruiter.post(
        f"/api/employer/applications/{application_id}/status/",
        {"status": "Under Review"},
        format="json",
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "Under Review"
    assert recruiter.post(
        f"/api/employer/applications/{application_id}/status/",
        {"status": "Hired"},
        format="json",
    ).status_code == 400

    notifications = candidate.get("/api/notifications/")
    assert notifications.status_code == 200
    assert len(notifications.json()) == 1
    notification_id = notifications.json()[0]["id"]
    assert {"id", "title", "body", "createdAt"} <= notifications.json()[0].keys()
    assert candidate.post(f"/api/notifications/{notification_id}/read/", format="json").status_code == 204
    assert recruiter.post(f"/api/notifications/{notification_id}/read/", format="json").status_code == 404
    assert candidate.post("/api/notifications/missing/read/", format="json").status_code == 404
    assert candidate.post("/api/employer/applications/missing/status/", {"status": "Rejected"}, format="json").status_code == 403
