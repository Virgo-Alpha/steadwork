from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from api.auth import authenticate, issue_token, validate_token
from api.store import get_store, reset_store


@pytest.fixture(autouse=True)
def clean_store():
    reset_store()
    yield
    reset_store()


def test_seed_data_is_deterministic_and_passwords_are_not_exposed():
    store = get_store()
    assert [company.id for company in store.companies] == ["company-acme", "company-orbit"]
    assert [job.id for job in store.jobs] == ["job-platform", "job-design"]
    assert [user.email for user in store.users] == [
        "candidate@example.com",
        "recruiter@example.com",
        "admin@example.com",
    ]
    assert authenticate("candidate@example.com", "candidate-password").role == "candidate"
    assert "password" not in store.users[0].to_dict()
    assert store.applications[0].candidate_id == "user-candidate"


def test_store_reset_does_not_leak_mutations():
    store = get_store()
    store.users[0].role = "admin"
    reset_store()
    assert get_store().users[0].role == "candidate"


def test_reset_store_invalidates_existing_tokens():
    user = authenticate("candidate@example.com", "candidate-password")
    token = issue_token(user)
    assert validate_token(token) is not None
    reset_store()
    assert validate_token(token) is None


def test_tokens_are_opaque_and_expire():
    user = authenticate("candidate@example.com", "candidate-password")
    token = issue_token(user, lifetime=timedelta(seconds=30))
    assert "." not in token
    assert validate_token(token).id == user.id
    assert validate_token(token, now=timezone.now() + timedelta(seconds=31)) is None


def test_login_and_protected_route_authorization():
    client = APIClient()
    assert client.get("/api/protected/candidate/").status_code == 401
    assert client.get("/api/protected/candidate/", HTTP_AUTHORIZATION="Basic abc").status_code == 401
    response = client.post("/api/auth/login/", {"email": "candidate@example.com", "password": "candidate-password"}, format="json")
    assert response.status_code == 200
    assert response.json()["token_type"] == "Bearer"
    assert "password" not in response.json()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.json()['access_token']}")
    assert client.get("/api/protected/candidate/").status_code == 200


def test_invalid_token_and_role_ownership_are_rejected():
    client = APIClient()
    assert client.get("/api/protected/candidate/").status_code == 401
    assert client.get("/api/protected/recruiter/user-candidate/").status_code == 401
