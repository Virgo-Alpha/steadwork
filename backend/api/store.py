"""Deterministic, resettable in-memory storage boundary."""

import os
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from datetime import timedelta
from django.utils import timezone
from .models import ActivityEvent, Application, Company, Job, Membership, Notification, User
from django.contrib.auth.hashers import make_password


_request_store: ContextVar[object | None] = ContextVar("steadwork_request_store", default=None)


@dataclass
class InMemoryStore:
    users: list[User]
    companies: list[Company]
    jobs: list[Job]
    applications: list[Application]
    profiles: dict[str, dict]
    saved_jobs: dict[str, set[str]]
    memberships: list[Membership]
    notifications: list[Notification]
    activity_events: list[ActivityEvent] = field(default_factory=list)


def _demo_observability_seed_enabled() -> bool:
    environment = os.getenv("STEADWORK_ENVIRONMENT", "development").strip().lower()
    enabled = os.getenv("STEADWORK_SEED_OBSERVABILITY_DATA", "false").strip().lower()
    return environment in {"development", "local"} and enabled in {"1", "true", "yes", "on"}


def _demo_activity_events(now):
    """Synthetic local history that makes business activity charts useful on first start."""
    if not _demo_observability_seed_enabled():
        return []

    def event(event_id, event_type, hours_ago, actor_id, role, subject_type=None,
              subject_id=None, application_method="none"):
        return ActivityEvent(
            id=f"demo-v1-{event_id}",
            event_type=event_type,
            occurred_at=now - timedelta(hours=hours_ago),
            actor_user_id=actor_id,
            actor_role=role,
            subject_type=subject_type,
            subject_id=subject_id,
            application_method=application_method,
            origin="demo",
        )

    return [
        event("register-candidate", "user_registered", 18, "user-candidate", "candidate", "user", "user-candidate"),
        event("register-recruiter", "user_registered", 120, "user-recruiter", "recruiter", "user", "user-recruiter"),
        event("register-admin", "user_registered", 144, "user-admin", "admin", "user", "user-admin"),
        event("login-candidate", "login_succeeded", 2, "user-candidate", "candidate", "user", "user-candidate"),
        event("login-recruiter", "login_succeeded", 72, "user-recruiter", "recruiter", "user", "user-recruiter"),
        event("login-admin", "login_succeeded", 144, "user-admin", "admin", "user", "user-admin"),
        event("publish-platform", "job_published", 7, "user-recruiter", "recruiter", "job", "job-platform"),
        event("publish-design", "job_published", 96, "user-recruiter", "recruiter", "job", "job-design"),
        event("submit-application", "application_submitted", 12, "user-candidate", "candidate", "application", "application-1"),
        event("withdraw-application", "application_withdrawn", 21, "user-candidate", "candidate", "application", "demo-application-withdrawn"),
        event("reject-application", "application_rejected", 22, "user-recruiter", "recruiter", "application", "demo-application-rejected"),
        event("external-apply", "external_apply_clicked", 5, "user-candidate", "candidate", "job", "job-design", "external"),
        event("unsave-job", "job_unsaved", 9, "user-candidate", "candidate", "job", "job-security"),
        event("save-job", "job_saved", 4, "user-candidate", "candidate", "job", "job-security"),
    ]


def _seed() -> InMemoryStore:
    now = timezone.now()
    return InMemoryStore(
        users=[
            User("user-candidate", "candidate@example.com", "candidate", make_password("candidate-password"), "Demo Candidate"),
            User("user-recruiter", "recruiter@example.com", "recruiter", make_password("recruiter-password"), "Demo Recruiter"),
            User("user-admin", "admin@example.com", "admin", make_password("admin-password"), "Demo Admin"),
        ],
        companies=[
            Company("company-acme", "Acme Technologies", "Cloud tools for modern teams.", "https://acme.example.com", "A", "#d7eddf"),
            Company("company-orbit", "Orbit Systems", "Designing products that move people forward.", "https://orbit.example.com", "O", "#e7ddf4"),
        ],
        jobs=[
            Job("job-platform", "company-acme", "Platform Engineer", "Build reliable services and developer tooling.", "Remote",
                120000, 160000, "USD", "Remote", "Full-time", "Senior", ["Python", "Django", "AWS"],
                ["Design APIs", "Improve reliability"], ["5+ years of backend experience"], ["Health insurance", "Flexible hours"],
                "Internal", None, "Published", timezone.now() - timedelta(days=2), timezone.now() + timedelta(days=30), 3),
            Job("job-design", "company-orbit", "Product Designer", "Create thoughtful experiences for growing teams.", "New York, NY",
                90000, 125000, "USD", "Hybrid", "Full-time", "Mid", ["Figma", "Research", "Prototyping"],
                ["Create prototypes", "Partner with engineering"], ["Portfolio of product work"], ["Learning budget"],
                "External", "https://orbit.example.com/jobs/design", "Published",
                timezone.now() - timedelta(days=5), timezone.now() + timedelta(days=45), 1),
            Job("job-security", "company-orbit", "Application Security Engineer", "Strengthen product security through practical reviews, threat modeling and developer tools.", "Remote",
                135000, 175000, "USD", "Remote", "Full-time", "Senior", ["Security", "Python", "AWS"],
                ["Review application architecture", "Build security automation"], ["Experience securing web services"], ["Health insurance", "Remote stipend"],
                "Internal", None, "Published", timezone.now() - timedelta(days=7), timezone.now() + timedelta(days=40), 0),
            Job("job-analytics", "company-orbit", "Product Data Analyst", "Turn product questions into clear analyses that help care teams improve patient experiences.", "Chicago, IL",
                95000, 120000, "USD", "Hybrid", "Contract", "Mid", ["SQL", "Analytics", "Python"],
                ["Build product dashboards", "Explain trends to partners"], ["Strong SQL and communication skills"], ["Flexible schedule"],
                "Internal", None, "Published", timezone.now() - timedelta(days=9), timezone.now() + timedelta(days=35), 0),
            Job("job-infrastructure", "company-orbit", "Cloud Infrastructure Engineer", "Make our cloud platform easier to operate, scale and understand.", "Austin, TX",
                125000, 160000, "USD", "Hybrid", "Part-time", "Mid", ["AWS", "Terraform", "Linux"],
                ["Improve infrastructure as code", "Support reliable releases"], ["Hands-on cloud operations experience"], ["Learning budget"],
                "Internal", None, "Published", timezone.now() - timedelta(days=11), timezone.now() + timedelta(days=32), 0),
            Job("job-research", "company-orbit", "UX Researcher", "Help teams understand the needs and constraints of people navigating complex care.", "Remote",
                105000, 138000, "USD", "Remote", "Contract", "Mid", ["User Research", "Interviews", "Accessibility"],
                ["Plan and run research studies", "Share findings with product teams"], ["Experience with qualitative research"], ["Caregiver leave"],
                "External", "https://orbit.example.com/jobs/research", "Published", timezone.now() - timedelta(days=13), timezone.now() + timedelta(days=28), 0),
            Job("job-devrel", "company-orbit", "Developer Advocate", "Help engineers build confidently with our APIs and platform tooling.", "Seattle, WA",
                115000, 150000, "USD", "Remote", "Contract", "Mid", ["Developer Relations", "Python", "Technical Writing"],
                ["Create developer guides", "Collect feedback from the community"], ["Clear technical communication"], ["Conference budget"],
                "Internal", None, "Published", timezone.now() - timedelta(days=15), timezone.now() + timedelta(days=30), 0),
            Job("job-accessibility", "company-orbit", "Accessibility Specialist", "Partner with design and engineering to make every care journey more accessible.", "Boston, MA",
                98000, 128000, "USD", "On-site", "Part-time", "Entry", ["Accessibility", "WCAG", "Testing"],
                ["Audit product experiences", "Coach teams on accessible patterns"], ["Working knowledge of WCAG"], ["Professional development"],
                "Internal", None, "Published", timezone.now() - timedelta(days=17), timezone.now() + timedelta(days=25), 0),
        ],
        applications=[] if os.getenv("STEADWORK_TEST_CLEAN_APPLICATIONS") == "1" else [
            Application("application-1", "job-platform", "user-candidate", "Applied",
                        "Candidate", "candidate@example.com", "candidate.pdf", "", now - timedelta(hours=12))
        ],
        profiles={},
        saved_jobs=(
            {"user-candidate": {"job-security"}}
            if _demo_observability_seed_enabled()
            else {}
        ),
        memberships=[
            Membership("user-recruiter", "company-acme", "recruiter"),
            Membership("user-admin", "company-acme", "admin"),
        ],
        notifications=[],
        activity_events=_demo_activity_events(now),
    )


_store = _seed()


def get_store() -> InMemoryStore:
    active = _request_store.get()
    if active is not None:
        return active
    from django.conf import settings

    if settings.STORE_BACKEND == "inmemory":
        return _store
    raise RuntimeError("The SQLite store is available only inside a request-scoped database session.")


def set_request_store(store: InMemoryStore) -> Token:
    return _request_store.set(store)


def clear_request_store(token: Token) -> None:
    _request_store.reset(token)


def reset_store() -> None:
    global _store
    _store = _seed()
    from .auth import revoke_all_tokens

    from django.conf import settings
    if settings.STORE_BACKEND != "inmemory":
        raise RuntimeError("reset_store() is available only when STEADWORK_STORE=inmemory.")

    revoke_all_tokens()

def application_status() -> str:
    """Report which persistence backend serves the current request."""
    from django.conf import settings
    return {"inmemory": "in-memory", "postgresql": "postgresql", "sqlite": "sqlite"}[settings.STORE_BACKEND]
