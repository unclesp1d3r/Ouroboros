#!/bin/bash
set -e
set -o pipefail

# Ouroboros Container Entrypoint Script
# Handles database initialization, migrations, and service routing

# Configuration with defaults
POSTGRES_HOST="${POSTGRES_SERVER:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-ouroboros}"
POSTGRES_DB="${POSTGRES_DB:-ouroboros}"
MAX_RETRIES="${DB_MAX_RETRIES:-30}"
RETRY_INTERVAL="${DB_RETRY_INTERVAL:-2}"

# Wait for PostgreSQL to be ready
wait_for_postgres() {
    echo "Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
    retries=0
    while ! pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -q; do
        retries=$((retries + 1))
        if [ "$retries" -ge "$MAX_RETRIES" ]; then
            echo "Error: PostgreSQL not available after ${MAX_RETRIES} attempts"
            exit 1
        fi
        echo "PostgreSQL not ready (attempt $retries/$MAX_RETRIES), retrying in ${RETRY_INTERVAL}s..."
        sleep "$RETRY_INTERVAL"
    done
    echo "PostgreSQL is ready!"
}

# Run database migrations
run_migrations() {
    echo "Running database migrations..."
    if uv run alembic upgrade head; then
        echo "Migrations completed successfully"
    else
        if [ "${IGNORE_MIGRATION_FAILURE:-false}" = "true" ]; then
            echo "WARNING: Migration failed but IGNORE_MIGRATION_FAILURE=true, continuing..."
            echo "WARNING: This should ONLY be used in development!"
        else
            echo "ERROR: Migration failed. Set IGNORE_MIGRATION_FAILURE=true to override (dev only)."
            exit 1
        fi
    fi
}

# Main execution
main() {
    # Skip database checks if explicitly disabled (useful for non-db containers)
    if [ "${SKIP_DB_WAIT:-false}" != "true" ]; then
        wait_for_postgres
    fi

    # Run migrations unless explicitly disabled
    if [ "${SKIP_MIGRATIONS:-false}" != "true" ]; then
        run_migrations
    fi

    # Route to appropriate service based on CONTAINER_ROLE
    # Using exec to replace shell process - signals are forwarded directly to application
    case "${CONTAINER_ROLE:-web}" in
        "web")
            echo "Starting web server..."
            exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
            ;;
        "web-dev")
            echo "Starting development web server with hot reload..."
            exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload "$@"
            ;;
        "worker")
            echo "Starting Celery worker..."
            exec uv run celery -A app.core.celery worker -l info "$@"
            ;;
        "scheduler")
            echo "Starting Celery beat scheduler..."
            exec uv run celery -A app.core.celery beat -l info "$@"
            ;;
        "shell")
            echo "Starting interactive shell..."
            exec /bin/bash "$@"
            ;;
        *)
            if [ $# -eq 0 ]; then
                echo "Error: Unrecognized CONTAINER_ROLE '${CONTAINER_ROLE:-}' and no command provided"
                echo "Valid roles: web, web-dev, worker, scheduler, shell"
                exit 1
            fi
            echo "Executing command: $*"
            exec "$@"
            ;;
    esac
}

# Execute main function with all arguments
main "$@"
