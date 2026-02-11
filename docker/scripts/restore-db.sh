#!/bin/bash
# Ouroboros Database Restore Script
# Restores PostgreSQL database from compressed backup

set -e
set -o pipefail

# Configuration with defaults
POSTGRES_HOST="${POSTGRES_SERVER:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-ouroboros}"
POSTGRES_DB="${POSTGRES_DB:-ouroboros}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"

# Validate required environment variables
if [ -z "${POSTGRES_PASSWORD:-}" ]; then
    echo "Error: POSTGRES_PASSWORD environment variable is required"
    exit 1
fi

# Check for backup file argument
BACKUP_FILE="${1:-}"

usage() {
    echo "Usage: $0 <backup_file>"
    echo ""
    echo "Restores a PostgreSQL database from a compressed backup file."
    echo ""
    echo "Arguments:"
    echo "  backup_file    Path to the .sql.gz backup file"
    echo ""
    echo "Environment variables:"
    echo "  POSTGRES_SERVER    Database host (default: postgres)"
    echo "  POSTGRES_PORT      Database port (default: 5432)"
    echo "  POSTGRES_USER      Database user (default: ouroboros)"
    echo "  POSTGRES_PASSWORD  Database password (required)"
    echo "  POSTGRES_DB        Database name (default: ouroboros)"
    echo ""
    echo "Available backups:"
    ls -lh "${BACKUP_DIR}/"*.sql.gz 2>/dev/null || echo "  No backups found in ${BACKUP_DIR}"
    exit 1
}

# Validate arguments
if [ -z "$BACKUP_FILE" ]; then
    echo "Error: No backup file specified"
    usage
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: ${BACKUP_FILE}"
    usage
fi

# Confirm restore operation
echo "WARNING: This will restore the database from backup."
echo ""
echo "  Host: ${POSTGRES_HOST}:${POSTGRES_PORT}"
echo "  Database: ${POSTGRES_DB}"
echo "  Backup file: ${BACKUP_FILE}"
echo ""

# Check if running interactively
if [ -t 0 ]; then
    read -r -p "Are you sure you want to continue? [y/N] " response
    case "$response" in
        [yY][eE][sS]|[yY])
            ;;
        *)
            echo "Restore cancelled"
            exit 0
            ;;
    esac
else
    echo "Non-interactive mode: proceeding with restore..."
fi

echo ""
echo "Starting database restore..."

# Restore from compressed backup
if gunzip -c "$BACKUP_FILE" | PGPASSWORD="${POSTGRES_PASSWORD}" psql \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --quiet; then

    echo "Restore completed successfully"
else
    echo "Error: Restore failed"
    exit 1
fi
