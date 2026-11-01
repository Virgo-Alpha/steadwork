from django.urls import include, path, re_path

from api.frontend import frontend_file

urlpatterns = [
    path("api/", include("api.urls")),
    re_path(r"^(?P<path>.*)$", frontend_file, name="frontend-file"),
]

