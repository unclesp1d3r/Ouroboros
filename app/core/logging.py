import re
import sys
from typing import TYPE_CHECKING, Any

from loguru import logger

from app.core.config import settings

if TYPE_CHECKING:
    from loguru import Record

__all__ = ["logger"]

# Sensitive fields that should be redacted from logs
SENSITIVE_FIELDS = {
    "authorization",
    "authorization_header",
    "bearer_token",
    "token",
    "password",
    "secret",
    "api_key",
    "access_token",
    "refresh_token",
    "client_secret",
    "private_key",
    "session_token",
    "auth_token",
    "jwt_token",
    "oauth_token",
    "x_api_key",
    "x_auth_token",
    "x_session_token",
}

# Patterns for token-like values that should be redacted
TOKEN_PATTERNS = [
    r"Bearer\s+[a-zA-Z0-9._-]+",  # Bearer tokens
    r"csa_[a-zA-Z0-9._-]+",  # Ouroboros agent tokens
    r"cst_[a-zA-Z0-9._-]+",  # Ouroboros TUI tokens
    r"[a-zA-Z0-9]{32,}",  # Long alphanumeric strings (likely tokens)
]


def redact_sensitive_data(record: dict[str, Any]) -> dict[str, Any]:
    """
    Redact sensitive data from log records.

    This function processes the 'extra' field of log records to remove or redact
    sensitive information like authorization headers, tokens, and other credentials.
    """
    if "extra" not in record:
        return record

    extra = record["extra"].copy()

    # Redact sensitive field names
    for field_name in list(extra.keys()):
        field_lower = field_name.lower()
        if any(sensitive in field_lower for sensitive in SENSITIVE_FIELDS):
            extra[field_name] = "[REDACTED]"

    # Redact sensitive values in dictionaries
    def redact_dict_values(data: object) -> object:
        if isinstance(data, dict):
            redacted = {}
            for key, value in data.items():
                key_lower = str(key).lower()
                if any(sensitive in key_lower for sensitive in SENSITIVE_FIELDS):
                    redacted[key] = "[REDACTED]"
                elif isinstance(value, (dict, list)):
                    redacted[key] = redact_dict_values(value)
                elif isinstance(value, str):
                    # Check for token patterns in string values
                    redacted_value = value
                    for pattern in TOKEN_PATTERNS:
                        redacted_value = re.sub(pattern, "[REDACTED]", redacted_value)
                    redacted[key] = redacted_value
                else:
                    redacted[key] = value
            return redacted
        if isinstance(data, list):
            return [redact_dict_values(item) for item in data]
        return data

    # Process all extra fields
    for key, value in extra.items():
        extra[key] = redact_dict_values(value)

    # Also redact sensitive patterns in the message field
    if "message" in record:
        redacted_message = record["message"]
        for pattern in TOKEN_PATTERNS:
            redacted_message = re.sub(pattern, "[REDACTED]", redacted_message)
        record["message"] = redacted_message

    record["extra"] = extra
    return record


def format_with_redaction(record: Record) -> str:
    """
    Custom format function that redacts sensitive data before formatting.
    """
    # Convert record to dict for redaction
    record_dict = {
        "time": record["time"],
        "level": record["level"],
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
        "message": record["message"],
        "extra": record["extra"],
    }

    # Redact sensitive data in the record
    redacted_record = redact_sensitive_data(record_dict)

    # Format the redacted record
    time_str = redacted_record["time"].strftime("%Y-%m-%d %H:%M:%S")
    level = redacted_record["level"].name
    module = redacted_record["module"]
    function = redacted_record["function"]
    line = redacted_record["line"]
    message = redacted_record["message"]

    return f"{time_str} | {level} | {module}:{function}:{line} - {message}"


logger.remove()
logger.add(
    sys.stderr,
    level=settings.log_level,
    format=format_with_redaction,
    enqueue=True,
    backtrace=True,
    diagnose=True,
)

if settings.log_to_file:
    logger.add(
        settings.log_file_path,
        level=settings.log_level,
        format=format_with_redaction,
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )
