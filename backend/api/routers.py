from rest_framework.decorators import api_view
from rest_framework.response import Response

from .auth import current_user
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

