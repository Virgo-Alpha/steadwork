import pytest
from django.contrib.auth.hashers import check_password
from rest_framework.test import APIClient

from api.store import get_store, reset_store


@pytest.fixture(autouse=True)
def clean_store():
    reset_store()
    yield
    reset_store()


def registration(**overrides):
    return {"name": "Taylor Reed", "email": "Taylor@example.com", "password": "long-password-123", "role": "candidate", **overrides}


def test_candidate_registration_hashes_password_and_returns_authenticated_verified_user():
    client = APIClient()
    response = client.post("/api/auth/register/", registration(), format="json")
    assert response.status_code == 201
    body = response.json()
    assert body["user"] == {"id": body["user"]["id"], "name": "Taylor Reed", "email": "taylor@example.com", "role": "candidate", "emailVerified": True}
    assert body["token_type"] == "Bearer"
    assert "long-password-123" not in str(body)
    user = next(item for item in get_store().users if item.email == "taylor@example.com")
    assert check_password("long-password-123", user.password_hash)
    assert get_store().profiles[user.id]["userId"] == user.id
    assert client.get("/api/auth/me/", HTTP_AUTHORIZATION=f"Bearer {body['access_token']}").status_code == 200


@pytest.mark.parametrize("payload", [
    {"name": "", "email": "a@example.com", "password": "12345678", "role": "candidate"},
    {"name": "A", "email": "not-an-email", "password": "12345678", "role": "candidate"},
    {"name": "A", "email": "a@example.com", "password": "short", "role": "candidate"},
    {"name": "A", "email": "a@example.com", "password": "12345678", "role": "admin"},
    {"name": "A", "email": "a@example.com", "password": "12345678", "role": "company"},
])
def test_registration_rejects_invalid_fields(payload):
    response = APIClient().post("/api/auth/register/", payload, format="json")
    assert response.status_code == 400
    assert not any(user.email == "a@example.com" for user in get_store().users)


def test_authentication_endpoints_reject_non_object_payloads_cleanly():
    client = APIClient()
    for path in ("/api/auth/login/", "/api/auth/register/"):
        response = client.post(path, ["unexpected", "array"], format="json")
        assert response.status_code == 400
        assert response.json()["detail"] == "Request body must be a JSON object."


def test_registration_normalizes_email_and_rejects_duplicates():
    client = APIClient()
    assert client.post("/api/auth/register/", registration(), format="json").status_code == 201
    duplicate = client.post("/api/auth/register/", registration(email=" taylor@EXAMPLE.com "), format="json")
    assert duplicate.status_code == 409
    assert len([user for user in get_store().users if user.email == "taylor@example.com"]) == 1


def test_company_registration_creates_company_membership_and_profile_access():
    client = APIClient()
    response = client.post("/api/auth/register/", registration(role="company", companyName="Fieldnote"), format="json")
    assert response.status_code == 201
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.json()['access_token']}")
    assert client.get("/api/employer/jobs/").json() == []
    assert any(company.name == "Fieldnote" for company in get_store().companies)


def test_verification_and_password_reset_endpoints_are_disabled():
    client = APIClient()
    for path in ("/api/auth/verify-email/", "/api/auth/password-reset/"):
        response = client.post(path, {"anything": "ignored"}, format="json")
        assert response.status_code == 410
        assert response.json()["detail"] == "Email verification and password reset are currently disabled."


def test_recommendations_require_candidate_and_rank_matching_skills():
    client = APIClient()
    assert client.get("/api/jobs/recommended/").status_code == 401
    login = client.post("/api/auth/login/", {"email": "candidate@example.com", "password": "candidate-password"}, format="json")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access_token']}")
    client.patch("/api/candidate/profile/", {"skills": ["Python"]}, format="json")
    jobs = client.get("/api/jobs/recommended/").json()
    assert jobs
    assert jobs[0]["id"] == "job-platform"


def test_logout_invalidates_tokens_across_the_user_session_version():
    client = APIClient()
    login = client.post("/api/auth/login/", {"email": "candidate@example.com", "password": "candidate-password"}, format="json")
    token = login.json()["access_token"]
    assert client.post("/api/auth/logout/", HTTP_AUTHORIZATION=f"Bearer {token}").status_code == 204
    assert client.get("/api/auth/me/", HTTP_AUTHORIZATION=f"Bearer {token}").status_code == 401
