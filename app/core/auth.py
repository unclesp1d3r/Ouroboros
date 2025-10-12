from datetime import UTC, datetime, timedelta
from uuid import UUID

import bcrypt
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from loguru import logger

from app.core.config import settings
from app.core.security import create_access_token as security_create_access_token

# Bcrypt has a maximum password length of 72 bytes
BCRYPT_MAX_PASSWORD_LENGTH = 72


class PasswordTooLongError(ValueError):
    """Raised when password exceeds bcrypt's 72-byte limit."""


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: The password to hash

    Returns:
        str: The hashed password

    Raises:
        PasswordTooLongError: If password exceeds 72 bytes when UTF-8 encoded
    """
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > BCRYPT_MAX_PASSWORD_LENGTH:
        raise PasswordTooLongError(
            f"Password exceeds maximum length of {BCRYPT_MAX_PASSWORD_LENGTH} bytes when UTF-8 encoded"
        )

    # Use bcrypt directly
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against a hash.

    Args:
        password: The password to verify
        hashed: The stored hash to verify against

    Returns:
        bool: True if password matches, False otherwise
    """
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > BCRYPT_MAX_PASSWORD_LENGTH:
        # Short-circuit: password too long, can't match
        return False

    # Use bcrypt directly
    return bcrypt.checkpw(password_bytes, hashed.encode("utf-8"))


def create_access_token(user_id: UUID) -> str:
    """Create a JWT access token.

    The token's expiration is determined by
    :data:`settings.ACCESS_TOKEN_EXPIRE_MINUTES`.
    """
    return security_create_access_token(str(user_id))


def decode_access_token(token: str) -> UUID:
    """Decode JWT access token and return user ID.

    Raises:
        ExpiredSignatureError: If token is expired
        JWTError: If token is invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise JWTError("Token missing subject")
        return UUID(user_id)
    except ExpiredSignatureError:
        logger.warning("JWT token expired during validation")
        raise
    except JWTError:
        logger.warning("JWT token invalid during validation")
        raise


def validate_token_expiration(token: str) -> bool:
    """Validate if token is expired without decoding the full payload.

    Returns:
        bool: True if token is valid and not expired, False if expired

    Raises:
        JWTError: If token is malformed or invalid
    """
    try:
        # Decode without verification to check expiration
        payload = jwt.decode(token, key="", options={"verify_signature": False})
        exp_timestamp = payload.get("exp")
        if not exp_timestamp:
            return False

        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=UTC)
        return datetime.now(UTC) < exp_datetime
    except (JWTError, ValueError, KeyError):
        return False


def get_token_expiration_time(token: str) -> datetime | None:
    """Get token expiration time.

    Returns:
        datetime | None: Token expiration time in UTC, or None if invalid
    """
    try:
        payload = jwt.decode(token, key="", options={"verify_signature": False})
        exp_timestamp = payload.get("exp")
        if not exp_timestamp:
            return None
        return datetime.fromtimestamp(exp_timestamp, tz=UTC)
    except (JWTError, ValueError, KeyError):
        return None


def is_token_refresh_needed(token: str, refresh_threshold_minutes: int = 15) -> bool:
    """Check if token should be refreshed based on remaining time.

    Args:
        token: JWT token to check
        refresh_threshold_minutes: Minutes before expiration to trigger refresh

    Returns:
        bool: True if token should be refreshed
    """
    exp_time = get_token_expiration_time(token)
    if not exp_time:
        return True  # Invalid token should be refreshed

    threshold_time = datetime.now(UTC) + timedelta(minutes=refresh_threshold_minutes)
    return exp_time <= threshold_time
