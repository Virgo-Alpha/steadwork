from pathlib import Path

from django.test import Client, override_settings


def test_root_serves_frontend_entrypoint(tmp_path: Path):
    (tmp_path / "index.html").write_text("<!doctype html><main>Steadwork app</main>")
    with override_settings(FRONTEND_STATIC_DIR=tmp_path):
        response = Client().get("/")

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/html")
    assert b"Steadwork app" in b"".join(response.streaming_content)


def test_direct_frontend_route_falls_back_to_entrypoint(tmp_path: Path):
    index = "<!doctype html><main>SPA entrypoint</main>"
    (tmp_path / "index.html").write_text(index)
    with override_settings(FRONTEND_STATIC_DIR=tmp_path):
        response = Client().get("/jobs/job-platform")

    assert response.status_code == 200
    assert b"".join(response.streaming_content).decode() == index


def test_existing_asset_is_served_with_its_content_type(tmp_path: Path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("console.log('built asset')")
    with override_settings(FRONTEND_STATIC_DIR=tmp_path):
        response = Client().get("/assets/app.js")

    assert response.status_code == 200
    assert "javascript" in response["Content-Type"]
    assert b"built asset" in b"".join(response.streaming_content)


def test_missing_static_asset_is_not_replaced_by_spa_fallback(tmp_path: Path):
    (tmp_path / "index.html").write_text("SPA entrypoint")
    with override_settings(FRONTEND_STATIC_DIR=tmp_path):
        response = Client().get("/assets/missing.js")

    assert response.status_code == 404
    assert b"SPA entrypoint" not in response.content


def test_missing_api_path_is_not_replaced_by_spa_fallback(tmp_path: Path):
    (tmp_path / "index.html").write_text("SPA entrypoint")
    with override_settings(FRONTEND_STATIC_DIR=tmp_path):
        response = Client().get("/api/no-such-route/")

    assert response.status_code == 404
    assert b"SPA entrypoint" not in response.content
