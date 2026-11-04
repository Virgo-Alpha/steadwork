"""Opaque, expiring bearer authentication for the in-memory milestone."""

from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.core import signing
from django.utils import timezone
from .models import User
from .store import get_store


_revocation_epoch = 0


def authenticate(email: str, password: str) -> User | None:
    user = next((u for u in get_store().users if u.email == email), None)
    return user if user and check_password(password, user.password_hash) else None


def issue_token(user: User, lifetime: timedelta | None = None) -> str:
    expires_at = timezone.now() + (lifetime if lifetime is not None else timedelta(
        seconds=getattr(settings, "TOKEN_LIFETIME_SECONDS", 3600)
    ))
    token = signing.dumps({"uid": user.id, "version": user.auth_version, "epoch": _revocation_epoch, "exp": expires_at.timestamp()},
                          salt="steadwork.access", compress=True)
    return token


def validate_token(token: str, now: datetime | None = None) -> User | None:
    try:
        payload = signing.loads(token, salt="steadwork.access")
    except signing.BadSignature:
        return None
    current = (now or timezone.now()).timestamp()
    if not isinstance(payload, dict) or not isinstance(payload.get("exp"), (int, float)) or payload["exp"] <= current:
        return None
    if payload.get("epoch") != _revocation_epoch:
        return None
    user = next((u for u in get_store().users if u.id == payload.get("uid")), None)
    if user is None or payload.get("version") != user.auth_version:
        return None
    return user


def current_user(request) -> User | None:
    header = request.META.get("HTTP_AUTHORIZATION", "")
    if not header:
        header = request.headers.get("Authorization", "")
    if not header and hasattr(request, "_request"):
        header = request._request.META.get("HTTP_AUTHORIZATION", "")
    parts = header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1]:
        return None
    return validate_token(parts[1])


def revoke_all_tokens() -> None:
    global _revocation_epoch
    _revocation_epoch += 1
