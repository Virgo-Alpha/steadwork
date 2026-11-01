from django.urls import path

from .routers import admin_probe, candidate_probe, health, login, recruiter_probe

urlpatterns = [
    path("health/", health, name="health"),
    path("auth/login/", login, name="login"),
    path("protected/candidate/", candidate_probe, name="candidate-probe"),
    path("protected/candidate/<str:user_id>/", candidate_probe, name="candidate-owned-probe"),
    path("protected/recruiter/", recruiter_probe, name="recruiter-probe"),
    path("protected/recruiter/<str:user_id>/", recruiter_probe, name="recruiter-owned-probe"),
    path("protected/admin/", admin_probe, name="admin-probe"),
    path("protected/admin/<str:user_id>/", admin_probe, name="admin-owned-probe"),
]
