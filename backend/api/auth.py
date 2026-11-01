"""Authentication boundary.

Authentication is intentionally not implemented in the skeleton; bearer
authentication is part of the next backend milestone.
"""


def current_user(request):
    return getattr(request, "user", None) if getattr(request, "user", None) else None

