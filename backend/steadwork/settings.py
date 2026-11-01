import os
from pathlib import Path
from api.database import get_database_url, get_store_backend

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "development-only-not-for-production"
DEBUG = True
ALLOWED_HOSTS = [host.strip() for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if host.strip()]

ROOT_URLCONF = "steadwork.urls"
WSGI_APPLICATION = "steadwork.wsgi.application"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "rest_framework",
    "api.apps.ApiConfig",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "api.middleware.SQLiteStoreMiddleware",
]

# Django's own ORM remains unused; application persistence is mediated by the
# SQLAlchemy repository behind api.store.
DATABASES = {"default": {"ENGINE": "django.db.backends.dummy"}}
STORE_BACKEND = get_store_backend()
DATABASE_URL = get_database_url()

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
ROOT_API_PATH = "/api/"
TOKEN_LIFETIME_SECONDS = 3600

REST_FRAMEWORK = {
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_AUTHENTICATION_CLASSES": [],
}
