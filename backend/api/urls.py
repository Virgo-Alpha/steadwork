from django.urls import path

from .routers import health

urlpatterns = [
    path("health/", health, name="health"),
]

