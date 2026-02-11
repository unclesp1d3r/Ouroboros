#!/bin/bash
# Ouroboros Database Backup Script
# Creates compressed PostgreSQL backups with timestamps

set -e
set -o pipefail

# Configuration with defaults
POSTGRES_HOST="${POSTGRES_SERVER:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-ouroboros}"
POSTGRES_DB="${POSTGRES_DB:-ouroboros}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"

# Validate required environment variables
if [ -z "${POSTGRES_PASSWORD:-}" ]; then
    echo "Error: POSTGRES_PASSWORD environment variable is required"
    exit 1
fi

# Generate backup filename with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${POSTGRES_DB}_${TIMESTAMP}.sql.gz"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

echo "Starting database backup..."
echo "  Host: ${POSTGRES_HOST}:${POSTGRES_PORT}"
echo "  Database: ${POSTGRES_DB}"
echo "  Output: ${BACKUP_FILE}"

# Perform backup with compression
if PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --format=plain \
    --no-owner \
    --no-acl \
    | gzip > "$BACKUP_FILE"; then

    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "Backup completed successfully: ${BACKUP_FILE} (${BACKUP_SIZE})"
else
    echo "Error: Backup failed"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# Clean up old backups if retention is configured
if [ "$RETENTION_DAYS" -gt 0 ]; then
    echo "Cleaning up backups older than ${RETENTION_DAYS} days..."
    find "$BACKUP_DIR" -name "${POSTGRES_DB}_*.sql.gz" -mtime +"$RETENTION_DAYS" -delete
    echo "Cleanup complete"
fi

# List current backups
echo ""
echo "Current backups:"
ls -lh "${BACKUP_DIR}/${POSTGRES_DB}_"*.sql.gz 2>/dev/null || echo "  No backups found"
