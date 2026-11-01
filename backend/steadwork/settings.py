from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "development-only-not-for-production"
DEBUG = True
ALLOWED_HOSTS: list[str] = []

ROOT_URLCONF = "steadwork.urls"
WSGI_APPLICATION = "steadwork.wsgi.application"

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "rest_framework",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
]

# The skeleton deliberately has no persistence dependency. A real database is
# introduced by the persistence task, not by this application bootstrap.
DATABASES = {"default": {"ENGINE": "django.db.backends.dummy"}}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
ROOT_API_PATH = "/api/"
TOKEN_LIFETIME_SECONDS = 3600

REST_FRAMEWORK = {
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_AUTHENTICATION_CLASSES": [],
}
