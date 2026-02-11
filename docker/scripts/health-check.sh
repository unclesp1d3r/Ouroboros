#!/bin/bash
# Ouroboros Container Health Check Script
# Returns exit code 0 if healthy, 1 if unhealthy

set -e

# Configuration with defaults
HEALTH_ENDPOINT="${HEALTH_ENDPOINT:-http://localhost:8000/health}"
TIMEOUT="${HEALTH_TIMEOUT:-10}"

# Check for curl availability
if ! command -v curl &> /dev/null; then
    echo "Health check error: curl is not installed"
    exit 1
fi

# Perform health check with diagnostic output
check_health() {
    local output
    local exit_code

    output=$(curl -sf --max-time "$TIMEOUT" "$HEALTH_ENDPOINT" 2>&1) || exit_code=$?
    exit_code=${exit_code:-0}

    if [ "$exit_code" -eq 0 ]; then
        echo "Health check passed: $HEALTH_ENDPOINT"
        exit 0
    else
        echo "Health check failed: $HEALTH_ENDPOINT"
        echo "  Exit code: $exit_code"
        # curl exit codes for common failures
        case $exit_code in
            6) echo "  Diagnosis: DNS resolution failed" ;;
            7) echo "  Diagnosis: Connection refused - is the app running?" ;;
            22) echo "  Diagnosis: HTTP error response" ;;
            28) echo "  Diagnosis: Request timed out after ${TIMEOUT}s" ;;
            *) echo "  Details: $output" ;;
        esac
        exit 1
    fi
}

check_health
