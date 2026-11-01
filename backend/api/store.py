"""Deterministic, resettable in-memory storage boundary."""

from dataclasses import dataclass
from datetime import timedelta
from django.utils import timezone
from .models import Application, Company, Job, User
from django.contrib.auth.hashers import make_password


@dataclass
class InMemoryStore:
    users: list[User]
    companies: list[Company]
    jobs: list[Job]
    applications: list[Application]


def _seed() -> InMemoryStore:
    return InMemoryStore(
        users=[
            User("user-candidate", "candidate@example.com", "candidate", make_password("candidate-password")),
            User("user-recruiter", "recruiter@example.com", "recruiter", make_password("recruiter-password")),
            User("user-admin", "admin@example.com", "admin", make_password("admin-password")),
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
        ],
        applications=[Application("application-1", "job-platform", "user-candidate", "applied")],
    )


_store = _seed()


def get_store() -> InMemoryStore:
    return _store


def reset_store() -> None:
    global _store
    _store = _seed()
    from .auth import revoke_all_tokens

    revoke_all_tokens()

def application_status() -> str:
    """Report the dependency-free store used by the bootstrap service."""
    return "in-memory"
