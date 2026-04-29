import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import Optional

from ...models import models
from ...core.security import hash_token


async def get_or_create_user(db: Session, github_user: dict) -> models.User:
    """
    Upsert a user record by GitHub ID.

    Args:
        db (Session): Database session.
        github_user (dict): Dict with keys: github_id, username, email, avatar_url.

    Returns:
        models.User: The existing or newly created User ORM object.

    Raises:
        KeyError: If required keys are missing from `github_user`.
    """
    github_id = str(github_user["github_id"])
    user = db.query(models.User).filter(models.User.github_id == github_id).first()

    if user:
        # Update profile fields in case they changed on GitHub
        user.username = github_user.get("username", user.username)
        user.email = github_user.get("email", user.email)
        user.avatar_url = github_user.get("avatar_url", user.avatar_url)
        user.last_login_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        return user

    new_user = models.User(
        github_id=github_id,
        username=github_user["username"],
        email=github_user.get("email"),
        avatar_url=github_user.get("avatar_url"),
        role="analyst",
        is_active=True,
        last_login_at=datetime.now(timezone.utc),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


async def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[models.User]:
    """
    Fetch a user by their UUID primary key.

    Args:
        db (Session): Database session.
        user_id (uuid.UUID): The user's UUID primary key.

    Returns:
        Optional[models.User]: The User object if found, otherwise None.
    """
    return db.query(models.User).filter(models.User.id == user_id).first()


async def store_refresh_token(
    db: Session,
    user_id: uuid.UUID,
    raw_token: str,
    expires_at: datetime,
) -> models.RefreshToken:
    """
    Hash and persist a refresh token.

    Args:
        db (Session): Database session.
        user_id (uuid.UUID): The owner's UUID.
        raw_token (str): The plaintext JWT (will be SHA-256 hashed).
        expires_at (datetime): When the token expires.

    Returns:
        models.RefreshToken: The persisted RefreshToken record.

    Raises:
        Exception: If database commit fails.
    """
    token_hash = hash_token(raw_token)
    db_token = models.RefreshToken(
        token_hash=token_hash,
        user_id=user_id,
        expires_at=expires_at,
        is_revoked=False,
    )
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token


async def get_refresh_token(
    db: Session, raw_token: str
) -> Optional[models.RefreshToken]:
    """
    Look up a refresh token record by its raw (unhashed) value.

    Args:
        db (Session): Database session.
        raw_token (str): The plaintext refresh token.

    Returns:
        Optional[models.RefreshToken]: The matching RefreshToken record, or None.
    """
    token_hash = hash_token(raw_token)
    return (
        db.query(models.RefreshToken)
        .filter(
            models.RefreshToken.token_hash == token_hash,
            models.RefreshToken.is_revoked == False,  # noqa: E712
        )
        .first()
    )


async def revoke_refresh_token(db: Session, raw_token: str) -> bool:
    """
    Mark a specific refresh token as revoked.

    Args:
        db (Session): Database session.
        raw_token (str): The plaintext refresh token to revoke.

    Returns:
        bool: True if the token was found and revoked, False otherwise.
    """
    token_hash = hash_token(raw_token)
    record = (
        db.query(models.RefreshToken)
        .filter(models.RefreshToken.token_hash == token_hash)
        .first()
    )
    if record:
        record.is_revoked = True
        db.commit()
        return True
    return False


async def revoke_all_user_tokens(db: Session, user_id: uuid.UUID) -> None:
    """
    Revoke every refresh token for a user (e.g., on logout-all).

    Args:
        db (Session): Database session.
        user_id (uuid.UUID): The user's UUID whose tokens should be revoked.

    Returns:
        None

    Raises:
        Exception: If the database update/commit fails.
    """
    db.query(models.RefreshToken).filter(
        models.RefreshToken.user_id == user_id,
        models.RefreshToken.is_revoked == False,  # noqa: E712
    ).update({"is_revoked": True})
    db.commit()
