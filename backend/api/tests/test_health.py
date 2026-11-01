import pytest
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient()


def test_health_endpoint_returns_successful_smoke_response(client):
    response = client.get("/api/health/")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "steadwork-backend",
        "store": "in-memory",
        "authenticated": False,
    }

