import os
from pathlib import Path
from api.database import get_database_url, get_store_backend

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_STATIC_DIR = Path(
    os.environ.get("STEADWORK_FRONTEND_DIR", BASE_DIR.parent / "frontend" / "dist" / "public")
)
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "development-only-not-for-production")
DEBUG = os.environ.get("DJANGO_DEBUG", "true").strip().lower() in {"1", "true", "yes", "on"}
ALLOWED_HOSTS = [host.strip() for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if host.strip()]
render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
if render_hostname:
    ALLOWED_HOSTS.append(render_hostname)
if not DEBUG and SECRET_KEY == "development-only-not-for-production":
    raise RuntimeError("DJANGO_SECRET_KEY must be configured when DJANGO_DEBUG is false")

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
EMAIL_TOKEN_LIFETIME_SECONDS = int(os.environ.get("EMAIL_TOKEN_LIFETIME_SECONDS", "86400"))
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "no-reply@steadwork.local")
email_host = os.environ.get("EMAIL_HOST", "").strip()
if email_host:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = email_host
    EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
    EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
    EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "true").strip().lower() in {"1", "true", "yes", "on"}
elif DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"

REST_FRAMEWORK = {
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_AUTHENTICATION_CLASSES": [],
}
