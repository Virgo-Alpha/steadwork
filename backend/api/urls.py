from django.urls import path

from .routers import admin_probe, candidate_probe, get_company, get_job, health, list_companies, list_jobs, login, recruiter_probe

urlpatterns = [
    path("health/", health, name="health"),
    path("auth/login/", login, name="login"),
    path("jobs/", list_jobs, name="jobs"),
    path("jobs/<str:job_id>/", get_job, name="job"),
    path("companies/", list_companies, name="companies"),
    path("companies/<str:company_id>/", get_company, name="company"),
    path("protected/candidate/", candidate_probe, name="candidate-probe"),
    path("protected/candidate/<str:user_id>/", candidate_probe, name="candidate-owned-probe"),
    path("protected/recruiter/", recruiter_probe, name="recruiter-probe"),
    path("protected/recruiter/<str:user_id>/", recruiter_probe, name="recruiter-owned-probe"),
    path("protected/admin/", admin_probe, name="admin-probe"),
    path("protected/admin/<str:user_id>/", admin_probe, name="admin-owned-probe"),
]
