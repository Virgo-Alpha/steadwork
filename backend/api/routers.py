from datetime import datetime, timezone as dt_timezone
import math
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .auth import authenticate, current_user, issue_token
from .store import application_status, get_store


_JOB_FILTERS = {"keyword", "location", "jobType", "remotePolicy", "experienceLevel", "companyId", "salaryMin", "skills", "postedWithin", "sort"}
_ENUMS = {
    "jobType": {"Full-time", "Part-time", "Contract", "Internship"},
    "remotePolicy": {"Remote", "Hybrid", "On-site"},
    "experienceLevel": {"Entry", "Mid", "Senior", "Lead"},
    "sort": {"recent", "salary", "relevance"},
}


def _bad(detail):
    return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)


def _utc(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        value = value.replace(tzinfo=dt_timezone.utc)
    return value.astimezone(dt_timezone.utc)


def _public_jobs(request):
    unknown = set(request.query_params) - _JOB_FILTERS
    if unknown:
        return None, _bad(f"Unknown query parameter: {sorted(unknown)[0]}.")
    values = request.query_params
    for key, allowed in _ENUMS.items():
        if key in values and values[key] not in allowed:
            return None, _bad(f"Invalid {key}.")
    numeric = {}
    for key in ("salaryMin", "postedWithin"):
        if key in values:
            try:
                number = float(values[key])
                if not math.isfinite(number) or number < 0:
                    raise ValueError
                numeric[key] = number
            except ValueError:
                return None, _bad(f"Invalid {key}.")
    skills = [item.strip() for item in values.get("skills", "").split(",") if item.strip()]
    now = datetime.now(dt_timezone.utc)
    jobs = [
        job for job in get_store().jobs
        if job.status == "Published" and job.deadline and _utc(job.deadline) > now
    ]
    company_by_id = {company.id: company for company in get_store().companies}
    keyword = values.get("keyword", "").strip().lower()
    if keyword:
        jobs = [job for job in jobs if keyword in f"{job.title} {job.description} {' '.join(job.skills or [])} {company_by_id.get(job.company_id).name if job.company_id in company_by_id else ''}".lower()]
    if values.get("location"):
        jobs = [job for job in jobs if values["location"].lower() in job.location.lower()]
    for attr, query_key in (("job_type", "jobType"), ("remote_policy", "remotePolicy"), ("experience_level", "experienceLevel"), ("company_id", "companyId")):
        if values.get(query_key):
            jobs = [job for job in jobs if getattr(job, attr) == values[query_key]]
    if "salaryMin" in numeric:
        jobs = [job for job in jobs if job.salary_max >= numeric["salaryMin"]]
    if skills:
        jobs = [job for job in jobs if all(any(skill.lower() == candidate.lower() for candidate in (job.skills or [])) for skill in skills)]
    if "postedWithin" in numeric:
        jobs = [job for job in jobs if (now - _utc(job.posted_at)).total_seconds() <= numeric["postedWithin"] * 86400]
    sort_key = values.get("sort", "recent")
    if sort_key == "salary":
        jobs.sort(key=lambda job: (-job.salary_max, job.id))
    else:
        jobs.sort(key=lambda job: (-_utc(job.posted_at).timestamp(), job.id))
    return jobs, None


@api_view(["GET"])
def health(request):
    """Return a dependency-free liveness response."""
    return Response(
        {
            "status": "ok",
            "service": "steadwork-backend",
            "store": application_status(),
            "authenticated": current_user(request) is not None,
        }
    )


@api_view(["POST"])
def login(request):
    user = authenticate(request.data.get("email", ""), request.data.get("password", ""))
    if not user:
        return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
    return Response({"access_token": issue_token(user), "token_type": "Bearer", "user": user.to_dict()})


@api_view(["GET"])
def list_jobs(request):
    jobs, error = _public_jobs(request)
    return error or Response([job.to_dict() for job in jobs])


@api_view(["GET"])
def get_job(request, job_id):
    jobs, error = _public_jobs(request)
    if error:
        return error
    job = next((item for item in jobs if item.id == job_id), None)
    return Response(job.to_dict()) if job else Response({"detail": "Job not found."}, status=status.HTTP_404_NOT_FOUND)


@api_view(["GET"])
def list_companies(request):
    if request.query_params:
        return _bad("Query parameters are not supported.")
    return Response([company.to_dict() for company in get_store().companies])


@api_view(["GET"])
def get_company(request, company_id):
    if request.query_params:
        return _bad("Query parameters are not supported.")
    company = next((item for item in get_store().companies if item.id == company_id), None)
    return Response(company.to_dict()) if company else Response({"detail": "Company not found."}, status=status.HTTP_404_NOT_FOUND)


def _protected(request, required_role: str, user_id: str | None = None):
    user = current_user(request)
    if user is None:
        return Response({"detail": "Authentication credentials were not provided."}, status=401)
    if user.role != required_role or (user_id is not None and user.id != user_id):
        return Response({"detail": "You do not have permission to perform this action."}, status=403)
    return Response({"user": user.to_dict(), "role": user.role})


@api_view(["GET"])
def candidate_probe(request, user_id=None):
    return _protected(request, "candidate", user_id)


@api_view(["GET"])
def recruiter_probe(request, user_id=None):
    return _protected(request, "recruiter", user_id)


@api_view(["GET"])
def admin_probe(request, user_id=None):
    return _protected(request, "admin", user_id)
