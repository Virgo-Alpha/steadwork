import re
from urllib.parse import urlparse, parse_qs

import pytest
from django.core import mail
from django.test import override_settings
from django.contrib.auth.hashers import check_password
from rest_framework.test import APIClient

from api.store import get_store, reset_store


@pytest.fixture(autouse=True)
def clean_store():
    reset_store()
    yield
    reset_store()


@pytest.fixture(autouse=True)
def email_backend():
    with override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
        mail.outbox = []
        yield


def registration(**overrides):
    return {"name": "Taylor Reed", "email": "Taylor@example.com", "password": "long-password-123", "role": "candidate", **overrides}


def token_from_mail(message):
    match = re.search(r"https?://\S+", message.body)
    assert match
    return parse_qs(urlparse(match.group(0)).query)["token"][0]


def test_candidate_registration_hashes_password_sends_verification_and_can_verify():
    client = APIClient()
    response = client.post("/api/auth/register/", registration(), format="json")
    assert response.status_code == 201
    body = response.json()
    assert body["user"] == {"id": body["user"]["id"], "name": "Taylor Reed", "email": "taylor@example.com", "role": "candidate", "emailVerified": False}
    assert body["token_type"] == "Bearer"
    assert "long-password-123" not in str(body)
    user = next(item for item in get_store().users if item.email == "taylor@example.com")
    assert check_password("long-password-123", user.password_hash)
    assert get_store().profiles[user.id]["userId"] == user.id
    assert len(mail.outbox) == 1

    verified = client.post("/api/auth/verify-email/", {"token": token_from_mail(mail.outbox[0])}, format="json")
    assert verified.status_code == 200
    assert verified.json()["emailVerified"] is True
    assert client.post("/api/auth/verify-email/", {"token": token_from_mail(mail.outbox[0])}, format="json").status_code == 400


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
    for path in ("/api/auth/login/", "/api/auth/register/", "/api/auth/verify-email/", "/api/auth/password-reset/"):
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


def test_email_delivery_failure_does_not_leave_in_memory_account():
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr("api.routers.send_mail", lambda *args, **kwargs: 0)
        response = APIClient().post("/api/auth/register/", registration(), format="json")
    assert response.status_code == 503
    assert not any(user.email == "taylor@example.com" for user in get_store().users)


def test_password_reset_is_non_enumerating_and_invalidates_old_password_and_token():
    client = APIClient()
    assert client.post("/api/auth/password-reset/", {"email": "missing@example.com"}, format="json").json() == client.post("/api/auth/password-reset/", {"email": "candidate@example.com"}, format="json").json()
    assert len(mail.outbox) == 1
    old_login = client.post("/api/auth/login/", {"email": "candidate@example.com", "password": "candidate-password"}, format="json")
    assert old_login.status_code == 200
    reset_token = token_from_mail(mail.outbox[0])
    assert client.post("/api/auth/password-reset/", {"token": reset_token, "password": "new-password-456"}, format="json").status_code == 204
    assert client.post("/api/auth/login/", {"email": "candidate@example.com", "password": "candidate-password"}, format="json").status_code == 401
    assert client.post("/api/auth/login/", {"email": "candidate@example.com", "password": "new-password-456"}, format="json").status_code == 200
    assert client.post("/api/auth/password-reset/", {"token": reset_token, "password": "another-password"}, format="json").status_code == 400
    assert client.get("/api/auth/me/", HTTP_AUTHORIZATION=f"Bearer {old_login.json()['access_token']}").status_code == 401


def test_action_tokens_reject_wrong_purpose_and_expired_tokens():
    client = APIClient()
    client.post("/api/auth/register/", registration(), format="json")
    client.post("/api/auth/password-reset/", {"email": "taylor@example.com"}, format="json")
    reset_token = token_from_mail(mail.outbox[1])
    assert client.post("/api/auth/verify-email/", {"token": reset_token}, format="json").status_code == 400
    verify_token = token_from_mail(mail.outbox[0])
    with override_settings(EMAIL_TOKEN_LIFETIME_SECONDS=-1):
        assert client.post("/api/auth/verify-email/", {"token": verify_token}, format="json").status_code == 400


def test_verification_link_remains_valid_after_logout():
    client = APIClient()
    registered = client.post("/api/auth/register/", registration(), format="json")
    verify_token = token_from_mail(mail.outbox[0])
    assert client.post("/api/auth/logout/", HTTP_AUTHORIZATION=f"Bearer {registered.json()['access_token']}").status_code == 204
    assert client.post("/api/auth/verify-email/", {"token": verify_token}, format="json").status_code == 200


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
