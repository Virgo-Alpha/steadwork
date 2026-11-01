from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .auth import authenticate, current_user, issue_token
from .store import application_status


@api_view(["GET"])
def health(request):
    """Return a dependency-free liveness response."""
    return Response(
        {
            "status": "ok",
            "service": "steadwork-backend",
            "store": application_status(),
            "authenticated": current_user(request) is not None,
        }
    )


@api_view(["POST"])
def login(request):
    user = authenticate(request.data.get("email", ""), request.data.get("password", ""))
    if not user:
        return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
    return Response({"access_token": issue_token(user), "token_type": "Bearer", "user": user.to_dict()})


def _protected(request, required_role: str, user_id: str | None = None):
    user = current_user(request)
    if user is None:
        return Response({"detail": "Authentication credentials were not provided."}, status=401)
    if user.role != required_role or (user_id is not None and user.id != user_id):
        return Response({"detail": "You do not have permission to perform this action."}, status=403)
    return Response({"user": user.to_dict(), "role": user.role})


@api_view(["GET"])
def candidate_probe(request, user_id=None):
    return _protected(request, "candidate", user_id)


@api_view(["GET"])
def recruiter_probe(request, user_id=None):
    return _protected(request, "recruiter", user_id)


@api_view(["GET"])
def admin_probe(request, user_id=None):
    return _protected(request, "admin", user_id)
