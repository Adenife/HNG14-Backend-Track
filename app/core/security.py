import hashlib
import secrets
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from fastapi import HTTPException, status

from .config import settings


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT access token.

    This function generates a JSON Web Token (JWT) with the provided data and an expiration time.
    The access token is signed using the secret key specified in the settings.

    Args:
        data (dict): The data to be included in the token payload.
        expires_delta (Optional[timedelta], optional): The expiration time of the token relative to the current time.
            If not provided, the token will expire after the number of minutes specified in the settings.

    Returns:
        str: The access token as a string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT refresh token.

    This function generates a JSON Web Token (JWT) with the provided data and an expiration time.
    The refresh token is signed using the secret key specified in the settings.

    Args:
        data (dict): The data to be included in the token payload.
        expires_delta (Optional[timedelta], optional): The expiration time of the token relative to the current time.
            If not provided, the token will expire after the number of minutes specified in the settings.

    Returns:
        str: The refresh token as a string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def verify_token(token: str, expected_type: str = "access") -> dict:
    """
    Decode and validate a JWT token.

    Args:
        token: The raw JWT string.
        expected_type: 'access' or 'refresh'

    Returns:
        The decoded payload dict.

    Raises:
        HTTPException 401 on any validation failure.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"status": "error", "message": "Invalid or expired token"},
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("type") != expected_type:
            raise credentials_exception
        if payload.get("sub") is None:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception


def hash_token(token: str) -> str:
    """SHA-256 hash a token for safe database storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_state() -> str:
    """Generate a cryptographically secure random state string for OAuth."""
    return secrets.token_urlsafe(32)


def generate_pkce_pair() -> tuple[str, str]:
    """
    Generate a PKCE code_verifier and code_challenge pair.

    Returns:
        (code_verifier, code_challenge) where challenge is S256 of verifier.
    """
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge
