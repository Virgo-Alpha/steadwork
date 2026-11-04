from mimetypes import guess_type
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, HttpResponseNotFound
from django.views.decorators.http import require_safe


def _inside(root: Path, relative: str) -> Path | None:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


@require_safe
def frontend_file(request, path: str = ""):
    """Serve built frontend files and route extensionless paths to the SPA."""
    if request.path == "/api" or request.path.startswith("/api/"):
        return HttpResponseNotFound("Not found")

    root = Path(settings.FRONTEND_STATIC_DIR)
    relative = path or "index.html"
    candidate = _inside(root, relative)
    if candidate is None:
        return HttpResponseNotFound("Not found")

    if candidate.is_file():
        content_type, _ = guess_type(candidate.name)
        response = FileResponse(candidate.open("rb"), content_type=content_type or "application/octet-stream")
        response["Cache-Control"] = (
            "public, max-age=31536000, immutable"
            if relative.startswith("assets/")
            else "no-cache, no-store, must-revalidate"
        )
        return response

    # Vite assets live under /assets/. Missing assets and any other path with a
    # file extension must stay 404s instead of returning the SPA HTML.
    if relative == "assets" or relative.startswith("assets/") or Path(relative).suffix:
        return HttpResponseNotFound("Not found")

    index = _inside(root, "index.html")
    if index is None or not index.is_file():
        return HttpResponseNotFound("Not found")
    response = FileResponse(index.open("rb"), content_type="text/html; charset=utf-8")
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response
