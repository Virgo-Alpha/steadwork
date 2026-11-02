from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from api.store import get_store, reset_store


@pytest.fixture(autouse=True)
def clean_store():
    reset_store()
    yield
    reset_store()


def test_public_jobs_are_contract_compatible_and_visible_only():
    response = APIClient().get("/api/jobs/")
    assert response.status_code == 200
    assert {"job-platform", "job-design", "job-security", "job-analytics", "job-infrastructure", "job-research", "job-devrel", "job-accessibility"} <= {job["id"] for job in response.json()}
    assert len(response.json()) == 8
    assert response.json()[0]["companyId"]
    assert all(job["status"] == "Published" for job in response.json())
    assert all("salaryMin" in job and "responsibilities" in job for job in response.json())


@pytest.mark.parametrize(
    "query, expected",
    [
        ({"keyword": "platform"}, {"job-platform"}),
        ({"location": "remote"}, {"job-platform", "job-security", "job-research"}),
        ({"jobType": "Full-time"}, {"job-platform", "job-design", "job-security"}),
        ({"remotePolicy": "Hybrid"}, {"job-design", "job-analytics"}),
        ({"experienceLevel": "Senior"}, {"job-platform", "job-security"}),
        ({"companyId": "company-orbit"}, {"job-design", "job-analytics", "job-research", "job-accessibility"}),
        ({"salaryMin": "130000"}, {"job-platform", "job-security"}),
        ({"skills": "Python,Django"}, {"job-platform"}),
    ],
)
def test_job_filters(query, expected):
    response = APIClient().get("/api/jobs/", query)
    assert response.status_code == 200
    assert {job["id"] for job in response.json()} == expected


def test_posted_within_zero_is_valid_and_empty():
    response = APIClient().get("/api/jobs/", {"postedWithin": "0"})
    assert response.status_code == 200
    assert response.json() == []


def test_sorting_and_tie_breakers_are_deterministic():
    store = get_store()
    now = timezone.now()
    for job in store.jobs:
        job.posted_at = now
    assert [j["id"] for j in APIClient().get("/api/jobs/", {"sort": "recent"}).json()[:2]] == [
        "job-design",
        "job-platform",
    ]
    assert [j["id"] for j in APIClient().get("/api/jobs/", {"sort": "salary"}).json()[:3]] == [
        "job-security",
        "job-infrastructure",
        "job-platform",
    ]
    assert [j["id"] for j in APIClient().get("/api/jobs/", {"sort": "relevance"}).json()[:2]] == [
        "job-design",
        "job-platform",
    ]


@pytest.mark.parametrize(
    "query",
    [{"jobType": "bad"}, {"salaryMin": "-1"}, {"postedWithin": "-1"}, {"sort": "bad"}, {"unknown": "x"}],
)
def test_invalid_query_values_return_json_400(query):
    response = APIClient().get("/api/jobs/", query)
    assert response.status_code == 400
    assert isinstance(response.json(), dict)
    assert "detail" in response.json()


def test_expired_and_unpublished_jobs_are_hidden_from_list_and_detail():
    store = get_store()
    store.jobs[0].status = "Draft"
    store.jobs[1].deadline = timezone.now() - timedelta(days=1)
    assert APIClient().get("/api/jobs/").json() == []
    assert APIClient().get("/api/jobs/job-platform/").status_code == 404
    assert APIClient().get("/api/jobs/job-design/").status_code == 404


def test_missing_resources_and_companies():
    client = APIClient()
    assert client.get("/api/jobs/missing/").status_code == 404
    assert client.get("/api/companies/").status_code == 200
    assert client.get("/api/companies/company-acme/").json()["name"] == "Acme Technologies"
    response = client.get("/api/companies/missing/")
    assert response.status_code == 404
    assert "detail" in response.json()
