# syntax=docker/dockerfile:1
# check=error=true

# Ouroboros FastAPI Backend Production Dockerfile
# Multi-stage build for optimized production image

# =============================================================================
# Stage 1: Builder - Install dependencies
# =============================================================================
FROM python:3.14-slim AS builder

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
FROM python:3.14-slim AS runtime

# Labels for container metadata
LABEL org.opencontainers.image.title="Ouroboros Backend"
LABEL org.opencontainers.image.description="Ouroboros FastAPI Backend Service"
LABEL org.opencontainers.image.vendor="CipherSwarm"

WORKDIR /app

# Install runtime dependencies only
# - curl: health checks
# - postgresql-client-17: pg_isready, pg_dump, psql for migrations and backups
#   (pinned to major version; client 17 is backward compatible with PostgreSQL 16 server)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    postgresql-client-17 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Create non-root user for security
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Copy virtual environment from builder stage
# With Python 3.14-slim base, uv uses system Python directly (no uv-managed Python needed)
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
