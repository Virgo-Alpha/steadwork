from datetime import datetime, timezone as dt_timezone
import math
from uuid import uuid4
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .auth import authenticate, current_user, issue_token
from dataclasses import replace

from .models import Application
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


def _candidate(request):
    user = current_user(request)
    if user is None:
        return None, Response({"detail": "Authentication credentials were not provided."}, status=401)
    if user.role != "candidate":
        return None, Response({"detail": "You do not have permission to perform this action."}, status=403)
    return user, None


_PROFILE_DEFAULTS = {
    "headline": "", "location": "", "skills": [], "experience": "",
    "education": "", "preferences": "", "cvFiles": [], "defaultCvId": "",
}


@api_view(["GET", "PATCH"])
def candidate_profile(request):
    user, error = _candidate(request)
    if error:
        return error
    store = get_store()
    profile = store.profiles.setdefault(user.id, {"userId": user.id, **_PROFILE_DEFAULTS})
    if request.method == "GET":
        return Response(profile)
    allowed = set(_PROFILE_DEFAULTS) | {"userId"}
    if set(request.data) - allowed:
        return _bad("Unknown profile field.")
    if "userId" in request.data and request.data["userId"] != user.id:
        return Response({"detail": "Profile ownership cannot be changed."}, status=403)
    for key in _PROFILE_DEFAULTS:
        if key not in request.data:
            continue
        value = request.data[key]
        if key in {"skills", "cvFiles"} and (not isinstance(value, list) or not all(isinstance(item, str) for item in value)):
            return _bad(f"Invalid {key}.")
        if key not in {"skills", "cvFiles"} and not isinstance(value, str):
            return _bad(f"Invalid {key}.")
        profile[key] = value
    return Response(profile)


@api_view(["GET", "POST"])
def saved_jobs(request):
    user, error = _candidate(request)
    if error:
        return error
    store = get_store()
    saved = store.saved_jobs.setdefault(user.id, set())
    if request.method == "GET":
        jobs = [job for job in store.jobs if job.id in saved]
        return Response([job.to_dict() for job in jobs])
    job_id = request.data.get("jobId")
    if not isinstance(job_id, str) or not job_id:
        return _bad("jobId is required.")
    if not next((job for job in store.jobs if job.id == job_id), None):
        return Response({"detail": "Job not found."}, status=404)
    saved.add(job_id)
    return Response(status=204)


@api_view(["DELETE"])
def unsave_job(request, job_id):
    user, error = _candidate(request)
    if error:
        return error
    saved = get_store().saved_jobs.setdefault(user.id, set())
    if job_id not in saved:
        return Response({"detail": "Saved job not found."}, status=404)
    saved.remove(job_id)
    return Response(status=204)


@api_view(["GET"])
def candidate_applications(request):
    user, error = _candidate(request)
    if error:
        return error
    return Response([app.to_dict() for app in get_store().applications if app.candidate_id == user.id])


def _application_input(data):
    required = ("jobId", "candidateName", "candidateEmail", "cvName", "coverLetter")
    if any(not isinstance(data.get(key), str) for key in required):
        return None, _bad("jobId, candidateName, candidateEmail, cvName and coverLetter are required.")
    values = {key: data[key].strip() if key != "coverLetter" else data[key] for key in required}
    if any(not values[key] for key in ("jobId", "candidateName", "candidateEmail", "cvName")):
        return None, _bad("jobId, candidateName, candidateEmail and cvName cannot be empty.")
    if "@" not in values["candidateEmail"]:
        return None, _bad("Invalid candidateEmail.")
    return values, None


def _eligible_job(job_id):
    job = next((item for item in get_store().jobs if item.id == job_id), None)
    if job is None:
        return None, Response({"detail": "Job not found."}, status=404)
    if job.status != "Published" or not job.deadline or _utc(job.deadline) <= datetime.now(dt_timezone.utc):
        return None, _bad("Applications are closed for this job.")
    if job.application_method != "Internal":
        return None, _bad("This job does not accept internal applications.")
    return job, None


@api_view(["POST"])
def create_application(request):
    user, error = _candidate(request)
    if error:
        return error
    values, error = _application_input(request.data)
    if error:
        return error
    if values["candidateEmail"].casefold() != user.email.casefold():
        return Response({"detail": "Application candidate does not match the current user."}, status=403)
    job, error = _eligible_job(values["jobId"])
    if error:
        return error
    if any(app.job_id == job.id and app.candidate_id == user.id for app in get_store().applications):
        return Response({"detail": "You have already applied to this job."}, status=409)
    app = Application(uuid4().hex, job.id, user.id, "Applied", values["candidateName"],
                      values["candidateEmail"].strip(), values["cvName"], values["coverLetter"], datetime.now(dt_timezone.utc))
    get_store().applications.append(app)
    job.application_count += 1
    return Response(app.to_dict(), status=201)


@api_view(["POST"])
def create_guest_application(request):
    values, error = _application_input(request.data)
    if error:
        return error
    job, error = _eligible_job(values["jobId"])
    if error:
        return error
    email = values["candidateEmail"].casefold()
    if any(app.job_id == job.id and app.candidate_id is None and app.candidate_email.casefold() == email
           for app in get_store().applications):
        return Response({"detail": "This email has already been used for this job."}, status=409)
    app = Application(uuid4().hex, job.id, None, "Applied", values["candidateName"],
                      email, values["cvName"], values["coverLetter"], datetime.now(dt_timezone.utc))
    get_store().applications.append(app)
    job.application_count += 1
    return Response(app.to_dict(), status=201)


@api_view(["POST"])
def withdraw_application(request, application_id):
    user, error = _candidate(request)
    if error:
        return error
    app = next((item for item in get_store().applications if item.id == application_id), None)
    if app is None:
        return Response({"detail": "Application not found."}, status=404)
    if app.candidate_id != user.id:
        return Response({"detail": "You do not have permission to withdraw this application."}, status=403)
    if app.status not in {"Applied", "Under Review", "Shortlisted"}:
        return _bad("This application cannot be withdrawn.")
    applications = get_store().applications
    index = applications.index(app)
    app = replace(app, status="Withdrawn")
    applications[index] = app
    return Response(app.to_dict())


@api_view(["GET"])
def candidate_probe(request, user_id=None):
    return _protected(request, "candidate", user_id)


@api_view(["GET"])
def recruiter_probe(request, user_id=None):
    return _protected(request, "recruiter", user_id)


@api_view(["GET"])
def admin_probe(request, user_id=None):
    return _protected(request, "admin", user_id)
