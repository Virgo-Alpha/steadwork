"""Low-cardinality OpenTelemetry instrumentation for user-facing actions."""

import logging
import os
import threading
import time
from functools import wraps
from datetime import datetime, timedelta, timezone as dt_timezone
from uuid import uuid4

from opentelemetry import metrics, trace
from opentelemetry.metrics import Observation
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.logging.handler import LoggingHandler
from opentelemetry.trace import Status, StatusCode


_logger = logging.getLogger("steadwork.user_actions")
_meter = metrics.get_meter("steadwork.api")
_tracer = trace.get_tracer("steadwork.api")
user_action_counter = _meter.create_counter(
    "steadwork.user_action",
    unit="1",
    description="Completed or failed user-facing API actions.",
)
business_event_counter = _meter.create_counter(
    "steadwork.business_event",
    unit="1",
    description="Successful user and marketplace business events.",
)
_business_gauges_configured = False
_activity_gauge_lock = threading.Lock()
_activity_gauge_cache = None
_activity_gauge_cache_time = 0.0
_BUSINESS_EVENT_TYPES = {
    "user_registered", "login_succeeded", "job_published", "application_submitted",
    "application_withdrawn", "application_rejected", "external_apply_clicked",
    "job_saved", "job_unsaved",
}
_BUSINESS_EVENT_ACTIONS = {
    "user_registered": "register",
    "login_succeeded": "login",
    "job_published": "job_status",
    "application_submitted": "submit_application",
    "application_withdrawn": "withdraw_application",
    "application_rejected": "review_application",
}


def _metric_role(role):
    return role if role in {"candidate", "recruiter", "admin", "company", "guest"} else "other"


def record_business_event(
    event_type, *, actor_user_id=None, actor_role="guest", subject_type=None,
    subject_id=None, application_method="none", occurred_at=None,
):
    """Persist an event and emit a low-cardinality metric/span event."""
    from .models import ActivityEvent
    from .store import get_store

    if event_type not in _BUSINESS_EVENT_TYPES:
        raise ValueError(f"Unknown business event type: {event_type}")
    role = _metric_role(actor_role)
    method = application_method if application_method in {"internal", "external"} else "none"
    event = ActivityEvent(
        id=uuid4().hex,
        event_type=event_type,
        occurred_at=occurred_at or datetime.now(dt_timezone.utc),
        actor_user_id=actor_user_id,
        actor_role=role,
        subject_type=subject_type,
        subject_id=subject_id,
        application_method=method,
    )
    get_store().activity_events.append(event)
    metric_attributes = {
        "event": event_type,
        "role": role,
        "application_method": method,
        "origin": "live",
    }
    business_event_counter.add(1, metric_attributes)
    trace.get_current_span().add_event("steadwork.business_event", metric_attributes)
    return event


def _activity_gauge_values(engine, now=None):
    """Return aggregate user/job gauges and rolling activity counts from SQL."""
    from sqlalchemy import func, select
    from sqlalchemy.orm import Session

    from .orm import ActivityEventRecord, JobRecord, SavedJobRecord, UserRecord

    now = now or datetime.now(dt_timezone.utc)
    values = {"users": [], "published_jobs": 0, "saved_jobs": 0,
              "active_users": {}, "applications_per_active_candidate": {},
              "rolling_business_events": {}, "rolling_user_actions": {}}
    with Session(engine) as session:
        values["users"] = list(session.execute(
            select(UserRecord.role, func.count()).group_by(UserRecord.role)
        ).all())
        values["published_jobs"] = session.scalar(
            select(func.count()).select_from(JobRecord).where(JobRecord.status == "Published")
        ) or 0
        values["saved_jobs"] = session.scalar(select(func.count()).select_from(SavedJobRecord)) or 0
        for window, age in (("24h", timedelta(hours=24)), ("7d", timedelta(days=7))):
            since = now - age
            event_counts = session.execute(
                select(
                    ActivityEventRecord.event_type,
                    ActivityEventRecord.origin,
                    func.count(),
                ).where(
                    ActivityEventRecord.occurred_at >= since,
                    ActivityEventRecord.occurred_at <= now,
                ).group_by(ActivityEventRecord.event_type, ActivityEventRecord.origin)
            ).all()
            values["rolling_business_events"][window] = [
                {"event": event_type, "origin": origin, "count": count}
                for event_type, origin, count in event_counts
            ]
            action_counts = {}
            for event_type, origin, count in event_counts:
                action = _BUSINESS_EVENT_ACTIONS.get(event_type)
                if action:
                    key = (action, "success", origin)
                    action_counts[key] = action_counts.get(key, 0) + count
            values["rolling_user_actions"][window] = [
                {"action": action, "outcome": outcome, "origin": origin, "count": count}
                for (action, outcome, origin), count in action_counts.items()
            ]
            values["active_users"][window] = session.scalar(
                select(func.count(func.distinct(ActivityEventRecord.actor_user_id))).where(
                    ActivityEventRecord.event_type == "login_succeeded",
                    ActivityEventRecord.actor_user_id.is_not(None),
                    ActivityEventRecord.occurred_at >= since,
                )
            ) or 0
            counts = session.execute(
                select(ActivityEventRecord.actor_user_id, func.count()).where(
                    ActivityEventRecord.event_type == "application_submitted",
                    ActivityEventRecord.actor_role == "candidate",
                    ActivityEventRecord.actor_user_id.is_not(None),
                    ActivityEventRecord.occurred_at >= since,
                ).group_by(ActivityEventRecord.actor_user_id)
            ).all()
            values["applications_per_active_candidate"][window] = (
                sum(count for _, count in counts) / len(counts) if counts else 0.0
            )
    return values


def _cached_activity_gauge_values(engine):
    global _activity_gauge_cache, _activity_gauge_cache_time
    current = time.monotonic()
    with _activity_gauge_lock:
        if _activity_gauge_cache is None or current - _activity_gauge_cache_time >= 4:
            _activity_gauge_cache = _activity_gauge_values(engine)
            _activity_gauge_cache_time = current
        return _activity_gauge_cache


def configure_business_metrics(engine):
    """Register bounded database-backed gauges once per API process."""
    global _business_gauges_configured
    if _business_gauges_configured:
        return

    _meter.create_observable_gauge(
        "steadwork.users",
        callbacks=[lambda _options: [
            Observation(count, {"role": _metric_role(role)})
            for role, count in _cached_activity_gauge_values(engine)["users"]
        ]],
        description="Current registered users grouped by account role.",
    )
    _meter.create_observable_gauge(
        "steadwork.published_jobs",
        callbacks=[lambda _options: [Observation(_cached_activity_gauge_values(engine)["published_jobs"])]],
        description="Current jobs with Published status.",
    )
    _meter.create_observable_gauge(
        "steadwork.saved_jobs",
        callbacks=[lambda _options: [Observation(_cached_activity_gauge_values(engine)["saved_jobs"])]],
        description="Current saved-job relationships.",
    )
    _meter.create_observable_gauge(
        "steadwork.active_users",
        callbacks=[lambda _options: [
            Observation(count, {"window": window})
            for window, count in _cached_activity_gauge_values(engine)["active_users"].items()
        ]],
        description="Distinct users with a successful login during the rolling window.",
    )
    _meter.create_observable_gauge(
        "steadwork.applications_per_active_candidate",
        callbacks=[lambda _options: [
            Observation(count, {"window": window})
            for window, count in _cached_activity_gauge_values(engine)["applications_per_active_candidate"].items()
        ]],
        description="Mean applications per candidate who applied during the rolling window.",
    )
    _meter.create_observable_gauge(
        "steadwork.business_events.rolling",
        callbacks=[lambda _options: [
            Observation(
                event["count"],
                {"event": event["event"], "origin": event["origin"], "window": window},
            )
            for window, events in _cached_activity_gauge_values(engine)["rolling_business_events"].items()
            for event in events
        ]],
        description="Persisted business event counts over rolling 24-hour and 7-day windows, including origin.",
    )
    _meter.create_observable_gauge(
        "steadwork.user_actions.rolling",
        callbacks=[lambda _options: [
            Observation(
                action["count"],
                {
                    "action": action["action"],
                    "outcome": action["outcome"],
                    "origin": action["origin"],
                    "window": window,
                },
            )
            for window, actions in _cached_activity_gauge_values(engine)["rolling_user_actions"].items()
            for action in actions
        ]],
        description="Persisted successful business actions over rolling windows, derived from activity history.",
    )
    _business_gauges_configured = True


def configure_otlp_logging():
    """Export Python log records with the same resource and active trace context."""
    if os.environ.get("OTEL_SDK_DISABLED", "false").lower() == "true":
        return
    if not os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT") and not os.environ.get(
        "OTEL_EXPORTER_OTLP_LOGS_ENDPOINT"
    ):
        return
    root_logger = logging.getLogger()
    if any(getattr(handler, "_steadwork_otel", False) for handler in root_logger.handlers):
        return

    from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter

    attributes = {"service.name": os.environ.get("OTEL_SERVICE_NAME", "steadwork-api")}
    for pair in os.environ.get("OTEL_RESOURCE_ATTRIBUTES", "").split(","):
        key, separator, value = pair.partition("=")
        if separator:
            attributes[key.strip()] = value.strip()
    provider = LoggerProvider(resource=Resource.create(attributes))
    provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter()))
    handler = LoggingHandler(level=logging.INFO, logger_provider=provider)
    handler._steadwork_otel = True
    root_logger.addHandler(handler)


def _outcome_for_status(status_code):
    if status_code < 400:
        return "success"
    if status_code >= 500:
        return "server_error"
    return {
        400: "validation_error",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        429: "rate_limited",
    }.get(status_code, "client_error")


def _active_trace_id():
    context = trace.get_current_span().get_span_context()
    return f"{context.trace_id:032x}" if context.is_valid else "0" * 32


def track_user_action(action, *, status_outcomes=None, when=None):
    """Record a bounded action span, counter and correlated summary log."""

    status_outcomes = status_outcomes or {}

    def decorate(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            request = args[0] if args else None
            if when is not None and not when(request, *args[1:], **kwargs):
                return view(*args, **kwargs)

            with _tracer.start_as_current_span(f"steadwork.{action}") as span:
                span.set_attribute("steadwork.user_action", action)
                try:
                    response = view(*args, **kwargs)
                except Exception as error:
                    outcome = "server_error"
                    span.set_attribute("steadwork.user_action.outcome", outcome)
                    span.set_attribute("exception.type", type(error).__name__)
                    span.set_status(Status(StatusCode.ERROR, type(error).__name__))
                    user_action_counter.add(1, {"action": action, "outcome": outcome})
                    _logger.error(
                        "user_action_failed trace_id=%s action=%s outcome=%s",
                        _active_trace_id(),
                        action,
                        outcome,
                        extra={"steadwork_action": action, "steadwork_outcome": outcome},
                    )
                    raise

                outcome = status_outcomes.get(response.status_code) or _outcome_for_status(
                    response.status_code
                )
                span.set_attribute("http.response.status_code", response.status_code)
                span.set_attribute("steadwork.user_action.outcome", outcome)
                if outcome == "server_error":
                    span.set_status(Status(StatusCode.ERROR))
                user_action_counter.add(1, {"action": action, "outcome": outcome})
                _logger.info(
                    "user_action_completed trace_id=%s action=%s outcome=%s",
                    _active_trace_id(),
                    action,
                    outcome,
                    extra={"steadwork_action": action, "steadwork_outcome": outcome},
                )
                return response

        return wrapped

    return decorate
