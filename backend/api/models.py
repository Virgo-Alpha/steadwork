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


@dataclass
class Company:
    id: str
    name: str
    description: str = ""
    website: str = ""
    logo: str = ""
    accent: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {key: getattr(self, key) for key in ("id", "name", "description", "website", "logo", "accent")}

@dataclass
class Job:
    id: str
    company_id: str
    title: str
    description: str = ""
    location: str = ""
    salary_min: float = 0
    salary_max: float = 0
    currency: str = "USD"
    remote_policy: str = "On-site"
    job_type: str = "Full-time"
    experience_level: str = "Mid"
    skills: list[str] | None = None
    responsibilities: list[str] | None = None
    qualifications: list[str] | None = None
    benefits: list[str] | None = None
    application_method: str = "Internal"
    external_apply_url: str | None = None
    status: str = "Draft"
    posted_at: Any = None
    deadline: Any = None
    application_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "companyId": self.company_id, "title": self.title,
            "description": self.description, "location": self.location,
            "salaryMin": self.salary_min, "salaryMax": self.salary_max, "currency": self.currency,
            "remotePolicy": self.remote_policy, "jobType": self.job_type,
            "experienceLevel": self.experience_level, "skills": self.skills or [],
            "responsibilities": self.responsibilities or [], "qualifications": self.qualifications or [],
            "benefits": self.benefits or [], "applicationMethod": self.application_method,
            "status": self.status,
            "postedAt": self.posted_at.isoformat() if hasattr(self.posted_at, "isoformat") else (self.posted_at or ""),
            "deadline": self.deadline.isoformat() if hasattr(self.deadline, "isoformat") else (self.deadline or ""),
            "applicationCount": self.application_count,
            **({"externalApplyUrl": self.external_apply_url} if self.external_apply_url else {}),
        }


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
