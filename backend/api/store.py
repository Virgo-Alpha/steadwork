"""Deterministic, resettable in-memory storage boundary."""

from dataclasses import dataclass
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
        companies=[Company("company-acme", "Acme Technologies"), Company("company-orbit", "Orbit Systems")],
        jobs=[
            Job("job-platform", "company-acme", "Platform Engineer"),
            Job("job-design", "company-orbit", "Product Designer"),
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
