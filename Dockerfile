# syntax=docker/dockerfile:1
# check=error=true

# Ouroboros FastAPI Backend Production Dockerfile
# Multi-stage build for optimized production image

# =============================================================================
# Stage 1: Builder - Install dependencies
# =============================================================================
FROM python:3.13-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install production dependencies only
RUN uv sync --frozen --no-dev

# =============================================================================
# Stage 2: Runtime - Minimal production image
# =============================================================================
FROM python:3.13-slim AS runtime

# Labels for container metadata
LABEL org.opencontainers.image.title="Ouroboros Backend"
LABEL org.opencontainers.image.description="Ouroboros FastAPI Backend Service"
LABEL org.opencontainers.image.vendor="CipherSwarm"

WORKDIR /app

# Install runtime dependencies only
# - curl: health checks
# - postgresql-client: pg_isready, pg_dump, psql for migrations and backups
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Create non-root user for security
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Copy uv-managed Python installation (required for venv symlinks to work)
# Must be at same path as builder stage since venv has absolute symlinks
COPY --from=builder /root/.local/share/uv/python /root/.local/share/uv/python

# Make uv Python accessible to non-root user
# The venv symlinks point to /root/.local/share/uv/python/...
RUN chmod a+rx /root /root/.local /root/.local/share /root/.local/share/uv \
    && chmod -R a+rX /root/.local/share/uv/python

# Copy virtual environment from builder stage
COPY --chown=appuser:appgroup --from=builder /app/.venv /app/.venv

# Copy dependency files
COPY --chown=appuser:appgroup pyproject.toml uv.lock ./

# Copy application code
COPY --chown=appuser:appgroup app ./app
COPY --chown=appuser:appgroup alembic ./alembic
COPY --chown=appuser:appgroup alembic.ini ./

# Copy entrypoint and utility scripts
COPY --chown=appuser:appgroup docker/scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY --chown=appuser:appgroup docker/scripts/health-check.sh /usr/local/bin/health-check.sh
RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/health-check.sh

# Create logs directory with proper permissions
RUN mkdir -p /app/logs && chown -R appuser:appgroup /app/logs

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    CONTAINER_ROLE=web

# Expose port
EXPOSE 8000

# Health check using health check script
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD /usr/local/bin/health-check.sh

# Use entrypoint script for initialization
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Default command (can be overridden)
CMD []
