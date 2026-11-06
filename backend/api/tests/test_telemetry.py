from api import telemetry
from opentelemetry.sdk.trace import TracerProvider
from rest_framework.response import Response
from rest_framework.test import APIClient
from unittest.mock import Mock


class RecordingCounter:
    def __init__(self):
        self.measurements = []

    def add(self, amount, attributes):
        self.measurements.append((amount, attributes))


def test_user_action_decorator_records_duplicate_registration_outcome(monkeypatch):
    counter = RecordingCounter()
    monkeypatch.setattr(telemetry, "user_action_counter", counter)

    @telemetry.track_user_action("register", status_outcomes={409: "duplicate_email"})
    def register_view(_request):
        return Response({"detail": "duplicate"}, status=409)

    response = register_view(object())

    assert response.status_code == 409
    assert counter.measurements == [(1, {"action": "register", "outcome": "duplicate_email"})]


def test_user_action_decorator_records_server_error_and_reraises(monkeypatch):
    counter = RecordingCounter()
    monkeypatch.setattr(telemetry, "user_action_counter", counter)

    @telemetry.track_user_action("apply")
    def failing_view(_request):
        raise RuntimeError("database unavailable")

    try:
        failing_view(object())
    except RuntimeError as error:
        assert str(error) == "database unavailable"
    else:
        raise AssertionError("the original exception must be re-raised")

    assert counter.measurements == [(1, {"action": "apply", "outcome": "server_error"})]


def test_user_action_log_contains_active_trace_id(monkeypatch):
    tracer = TracerProvider().get_tracer("telemetry-test")
    monkeypatch.setattr(telemetry, "_tracer", tracer)
    logger = Mock()
    monkeypatch.setattr(telemetry, "_logger", logger)

    @telemetry.track_user_action("register")
    def register_view(_request):
        return Response({"ok": True}, status=201)

    with tracer.start_as_current_span("http.request") as request_span:
        response = register_view(object())
        expected_trace_id = f"{request_span.get_span_context().trace_id:032x}"

    assert response.status_code == 201
    assert logger.info.call_args.args[1] == expected_trace_id


def test_duplicate_registration_returns_conflict_and_records_expected_outcome(monkeypatch):
    counter = RecordingCounter()
    monkeypatch.setattr(telemetry, "user_action_counter", counter)
    client = APIClient()
    data = {
        "name": "Duplicate Example",
        "email": "duplicate-observability@example.com",
        "password": "secure-password",
        "role": "candidate",
    }

    first = client.post("/api/auth/register/", data, format="json")
    duplicate = client.post("/api/auth/register/", data, format="json")

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert counter.measurements == [
        (1, {"action": "register", "outcome": "success"}),
        (1, {"action": "register", "outcome": "duplicate_email"}),
    ]
