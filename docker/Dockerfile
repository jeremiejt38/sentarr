# syntax=docker/dockerfile:1
FROM node:22-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS backend
WORKDIR /app/backend

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY backend/pyproject.toml backend/uv.lock* ./
COPY backend/README.md ./
COPY backend/sentarr ./sentarr
RUN uv sync --no-dev

COPY --from=frontend-builder /app/frontend/dist ./static

COPY backend/alembic.ini ./alembic.ini
COPY backend/alembic ./alembic

ENV PYTHONUNBUFFERED=1
ENV PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uv", "run", "uvicorn", "sentarr.main:app", "--host", "0.0.0.0", "--port", "8000"]
