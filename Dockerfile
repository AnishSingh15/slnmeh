# syntax=docker/dockerfile:1

# ---- Frontend build ---------------------------------------------------------------
FROM node:24-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Runtime ----------------------------------------------------------------------
FROM python:3.12-slim AS runtime
COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /usr/local/bin/uv
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1 \
    PYTHONPATH=/app/backend \
    PATH="/app/backend/.venv/bin:$PATH" \
    WINDDESK_DATA_DIR=/app/data/snapshot \
    WINDDESK_STATIC_DIR=/app/static \
    PORT=8000
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./backend/
RUN cd backend && uv sync --frozen --no-dev --no-install-project
COPY backend/winddesk ./backend/winddesk
COPY data/snapshot ./data/snapshot
COPY --from=frontend /app/frontend/dist ./static
RUN useradd --create-home --uid 10001 app
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
  CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/api/health', timeout=2)"
CMD ["sh", "-c", "exec uvicorn --factory winddesk.main:create_app --host 0.0.0.0 --port ${PORT} --proxy-headers"]
