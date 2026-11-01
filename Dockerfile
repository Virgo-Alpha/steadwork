# syntax=docker/dockerfile:1

FROM node:22-alpine AS frontend-build

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS backend-runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/steadwork-venv \
    STEADWORK_FRONTEND_DIR=/opt/steadwork/frontend

WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project
COPY backend/ ./
COPY --from=frontend-build /build/frontend/dist/public/ /opt/steadwork/frontend/

RUN useradd --create-home --uid 10001 steadwork \
    && chown -R steadwork:steadwork /app /opt/steadwork
USER steadwork

EXPOSE 8000
CMD ["sh", "-c", "uv run --no-sync alembic upgrade head && uv run --no-sync python manage.py runserver 0.0.0.0:8000"]
