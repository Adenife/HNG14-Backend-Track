from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import uuid

from .database import get_db
from .security import verify_token
from ..models import models
from ..models.cruds import userCrud

# Bearer token extractor — also checks cookies for the web portal
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> models.User:
    """
    Retrieves the current user's information.

    Returns:
        dict: A dictionary containing the current user's information, including their username (str), email (str),
            and role (str). If the user is not logged in, an empty dictionary is returned.

    Raises:
        KeyError: If the user's information cannot be retrieved from the session.

    Notes:
        - This function assumes that the user's information is stored in the session under the key 'user_info'.
        - The function checks if the 'user_info' key is present in the session and retrieves the corresponding value.
        - If the 'user_info' key is not found, a KeyError is raised.
        - The function returns an empty dictionary if the user is not logged in.
    """
    token: Optional[str] = None

    if credentials:
        token = credentials.credentials
    else:
        # Try HTTP-only cookie (web portal)
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"status": "error", "message": "Authentication required"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(token, expected_type="access")
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"status": "error", "message": "Missing authentication token"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        # user_id = payload.get("sub")
        user_id = uuid.UUID(payload["sub"])
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"status": "error", "message": "Invalid user identifier in token"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await userCrud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"status": "error", "message": "User not found"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"status": "error", "message": "Account is inactive"},
        )

    return user


async def require_admin(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """Dependency that enforces the admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"status": "error", "message": "Admin access required"},
        )
    return current_user


async def require_analyst_or_admin(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """Dependency that allows analyst or admin (read access)."""
    if current_user.role not in ("admin", "analyst"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"status": "error", "message": "Access denied"},
        )
    return current_user
