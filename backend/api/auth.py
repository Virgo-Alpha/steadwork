"""Opaque, expiring bearer authentication for the in-memory milestone."""

import secrets
from datetime import datetime, timedelta
from dataclasses import dataclass
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from .models import User
from .store import get_store


@dataclass
class TokenSession:
    user_id: str
    expires_at: datetime


_tokens: dict[str, TokenSession] = {}


def authenticate(email: str, password: str) -> User | None:
    user = next((u for u in get_store().users if u.email == email), None)
    return user if user and check_password(password, user.password_hash) else None


def issue_token(user: User, lifetime: timedelta | None = None) -> str:
    now = timezone.now()
    _tokens_copy = {
        token: session for token, session in _tokens.items() if session.expires_at > now
    }
    _tokens.clear()
    _tokens.update(_tokens_copy)
    token = secrets.token_urlsafe(32)
    _tokens[token] = TokenSession(
        user.id, now + (lifetime or timedelta(seconds=getattr(settings, "TOKEN_LIFETIME_SECONDS", 3600)))
    )
    return token


def validate_token(token: str, now: datetime | None = None) -> User | None:
    session = _tokens.get(token)
    current = now or timezone.now()
    if not session or session.expires_at <= current:
        _tokens.pop(token, None)
        return None
    return next((u for u in get_store().users if u.id == session.user_id), None)


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
    _tokens.clear()
