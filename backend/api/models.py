"""Small domain objects used by the dependency-free in-memory backend."""

from dataclasses import dataclass
from typing import Any


@dataclass
class User:
    id: str
    email: str
    role: str
    password_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "email": self.email, "role": self.role}


@dataclass(frozen=True)
class Company:
    id: str
    name: str


@dataclass(frozen=True)
class Job:
    id: str
    company_id: str
    title: str


@dataclass(frozen=True)
class Application:
    id: str
    job_id: str
    candidate_id: str
    status: str


@dataclass(frozen=True)
class HealthStatus:
    status: str
    service: str
