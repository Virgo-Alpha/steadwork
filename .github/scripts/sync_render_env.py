"""Merge the deployment-owned settings into a Render service's env vars."""

from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


API_ROOT = "https://api.render.com/v1"


def api_request(method: str, url: str, api_key: str, body: object | None = None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            payload = response.read()
    except HTTPError as error:
        raise RuntimeError(f"Render API returned HTTP {error.code} for {method} {url}") from None
    except (TimeoutError, URLError) as error:
        raise RuntimeError(f"Render API request failed: {error.reason if isinstance(error, URLError) else error}") from None
    if not payload:
        return None
    return json.loads(payload)


def main() -> int:
    api_key = os.environ["RENDER_API_KEY"]
    service_id = os.environ["RENDER_SERVICE_ID"]
    database_url = os.environ["DATABASE_URL"]
    allowed_hosts = os.environ["DJANGO_ALLOWED_HOSTS"]
    desired = {
        "DATABASE_URL": database_url,
        "STEADWORK_STORE": "postgresql",
        "DJANGO_DEBUG": "false",
        "DJANGO_ALLOWED_HOSTS": allowed_hosts,
    }

    # Use Render's per-variable endpoint rather than its list-replacement
    # endpoint. This leaves generated and user-managed secrets untouched.
    for key, value in desired.items():
        encoded_key = quote(key, safe="")
        api_request(
            "PUT",
            f"{API_ROOT}/services/{service_id}/env-vars/{encoded_key}",
            api_key,
            {"value": value},
        )
    print("Synchronized deployment-owned Render environment variables.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, RuntimeError, json.JSONDecodeError) as error:
        print(f"Render environment synchronization failed: {error}", file=sys.stderr)
        raise SystemExit(1)
