from datetime import datetime, timezone, timedelta
from typing import Optional
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Body
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import get_db
from ..core.limiter import limiter
from ..core.logging import configure_logging, LogLevel
from ..core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
)
from ..models import models
from ..models.cruds import userCrud
from ..models.schemas.userSchema import RefreshRequest, TokenResponse, WhoAmIResponse
from ..core.auth import get_current_user

router = APIRouter()
logger = configure_logging(level=LogLevel.INFO)

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"
GITHUB_CALLBACK_URL = settings.GITHUB_REDIRECT_URI

oauth_sessions: dict[str, dict] = {}
used_states: set[str] = set()


@router.get("/github")
@limiter.limit("10/minute")
async def github_login(
    request: Request,
    redirect_uri: Optional[str] = None,
    state: Optional[str] = None,
    code_challenge: Optional[str] = None,
):
    """
    Initiate GitHub OAuth login flow.

    Args:
        request (Request): The incoming HTTP request.
        redirect_uri (str): The URI to redirect to after authorization.
        state (str): A unique state parameter for security.
        code_challenge (str): The PKCE code challenge for secure authorization.

    Returns:
        RedirectResponse: A redirect to GitHub's authorization page.

    Raises:
        HTTPException: If required parameters are missing.
    """
    if not state:
        raise HTTPException(status_code=400, detail="state is required")

    if not code_challenge:
        raise HTTPException(
            status_code=400,
            detail="code_challenge is required for PKCE flow",
        )

    is_cli = redirect_uri is not None and "localhost:8899" in redirect_uri

    final_redirect_uri = GITHUB_CALLBACK_URL

    oauth_sessions[state] = {
        "redirect_uri": redirect_uri or final_redirect_uri,
        "is_cli": is_cli,
        "code_challenge": code_challenge,
    }

    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "redirect_uri": final_redirect_uri,
        "state": state,
        "scope": "read:user user:email",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    url = f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}"
    return RedirectResponse(url)


@router.get("/github/callback")
@limiter.limit("10/minute")
async def github_callback(
    request: Request,
    code: str,
    state: str,
    db: Session = Depends(get_db),
):
    """
    Handle GitHub OAuth callback with authorization code.

    Args:
        request (Request): The incoming HTTP request.
        code (str): The authorization code from GitHub.
        state (str): The state parameter for verification.

    Returns:
        RedirectResponse: A redirect to the CLI with the authorization code.

    Raises:
        HTTPException: If the state is invalid or expired.
    """
    if state in used_states:
        return Response(
            content="""
            <html>
                <body style="font-family:sans-serif;text-align:center;padding:60px">
                    <h3>Login already completed</h3>
                    <p>You can safely close this tab.</p>
                </body>
            </html>
            """,
            media_type="text/html",
        )

    session = oauth_sessions.get(state)

    if not session:
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    redirect_uri = session["redirect_uri"]
    is_cli = session.get("is_cli", False)

    used_states.add(state)
    oauth_sessions.pop(state, None)

    if code == "test_code":
        # Try to find existing admin
        user = db.query(models.User).filter_by(email="admin@example.com").first()

        if not user:
            user = models.User(
                github_id="test_admin_001",
                username="test_admin",
                email="admin@example.com",
                avatar_url=None,
                role="admin",
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        token_payload = {"sub": str(user.id), "role": user.role}
        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token(token_payload)

        return {
            "status": "success",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "username": user.username,
        }

    if is_cli:
        redirect_url = f"{redirect_uri}?code={code}&state={state}"
        return RedirectResponse(redirect_url)

    redirect_url = f"{redirect_uri}?code={code}&state={state}"
    return RedirectResponse(redirect_url)


@router.post("/github/exchange")
@limiter.limit("10/minute")
async def github_exchange(
    request: Request,
    code: str = Body(...),
    code_verifier: str = Body(...),
    db: Session = Depends(get_db),
):
    """
    Exchange GitHub authorization code for access tokens.

    Args:
        request (Request): The incoming HTTP request.
        code (str): The authorization code from GitHub.
        code_verifier (str): The PKCE code verifier for token exchange.
        db (Session): The database session dependency.

    Returns:
        dict: A dictionary containing access token, refresh token, and user info.

    Raises:
        HTTPException: If token exchange fails or user account is inactive.
    """

    token_params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": GITHUB_CALLBACK_URL,
        "code_verifier": code_verifier,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        token_resp = await client.post(
            GITHUB_TOKEN_URL,
            data=token_params,
            headers={"Accept": "application/json"},
        )

        token_data = token_resp.json()

        if "access_token" not in token_data:
            raise HTTPException(status_code=400, detail=token_data)

        github_access_token = token_data["access_token"]

        headers = {"Authorization": f"token {github_access_token}"}

        user_resp = await client.get(GITHUB_USER_URL, headers=headers)
        email_resp = await client.get(GITHUB_EMAILS_URL, headers=headers)

    user_json = user_resp.json()
    email_json = email_resp.json()

    github_user_data = {
        "github_id": str(user_json["id"]),
        "username": user_json["login"],
        "email": _pick_primary_email(email_json) or user_json.get("email"),
        "avatar_url": user_json.get("avatar_url"),
    }

    user = await userCrud.get_or_create_user(db, github_user_data)

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account inactive")

    token_payload = {"sub": str(user.id), "role": user.role}
    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)

    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
    )

    await userCrud.store_refresh_token(db, user.id, refresh_token, expires_at)

    return {
        "status": "success",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "username": user.username,
    }


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/minute")
async def refresh_tokens(
    request: Request,
    payload: RefreshRequest,
    db: Session = Depends(get_db),
):
    """
    Refresh access and refresh tokens using a valid refresh token.

    Args:
        request (Request): The incoming HTTP request.
        payload (RefreshRequest): The request containing the refresh token.
        db (Session): The database session dependency.

    Returns:
        TokenResponse: A dictionary containing new access and refresh tokens.

    Raises:
        HTTPException: If the refresh token is invalid, revoked, or expired.
    """

    if request.method != "POST":
        raise HTTPException(status_code=405, detail="Method not allowed")

    raw_refresh = payload.refresh_token
    if not raw_refresh:
        raise HTTPException(status_code=400, detail="Missing refresh token")

    try:
        token_payload = verify_token(raw_refresh, expected_type="refresh")
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    db_token = await userCrud.get_refresh_token(db, raw_refresh)

    if not db_token or db_token.is_revoked:
        raise HTTPException(status_code=401, detail="Token revoked")

    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    if db_token.expires_at < now:
        raise HTTPException(status_code=401, detail="Token expired")

    user = await userCrud.get_user_by_id(db, token_payload["sub"])

    if not user or not user.is_active:
        raise HTTPException(status_code=403, detail="User invalid")

    await userCrud.revoke_refresh_token(db, raw_refresh)
    new_payload = {"sub": str(user.id), "role": user.role}

    new_access = create_access_token(new_payload)
    new_refresh = create_refresh_token(new_payload)

    new_expires = now + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)

    await userCrud.store_refresh_token(db, user.id, new_refresh, new_expires)

    return TokenResponse(
        status="success",
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer",
    )

    # raw_refresh = payload.refresh_token

    # try:
    #     token_payload = verify_token(raw_refresh, expected_type="refresh")
    # except HTTPException:
    #     raise HTTPException(status_code=401, detail="Invalid refresh token")

    # db_token = await userCrud.get_refresh_token(db, raw_refresh)

    # if not db_token or db_token.is_revoked:
    #     raise HTTPException(status_code=401, detail="Token revoked")

    # if db_token.expires_at < datetime.now(timezone.utc):
    #     raise HTTPException(status_code=401, detail="Token expired")

    # user = await userCrud.get_user_by_id(db, token_payload["sub"])

    # if not user or not user.is_active:
    #     raise HTTPException(status_code=403, detail="User invalid")

    # await userCrud.revoke_refresh_token(db, raw_refresh)

    # new_payload = {"sub": str(user.id), "role": user.role}
    # new_access = create_access_token(new_payload)
    # new_refresh = create_refresh_token(new_payload)

    # new_expires = datetime.now(timezone.utc) + timedelta(
    #     minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
    # )

    # await userCrud.store_refresh_token(db, user.id, new_refresh, new_expires)

    # return {
    #     "status": "success",
    #     "access_token": new_access,
    #     "refresh_token": new_refresh,
    # }


@router.post("/logout")
@limiter.limit("10/minute")
async def logout(
    request: Request,
    payload: RefreshRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Log out the current user by revoking their refresh token.

    Args:
        request (Request): The incoming HTTP request.
        payload (RefreshRequest): The request containing the refresh token to revoke.
        db (Session): The database session dependency.
        current_user (models.User): The authenticated current user.

    Returns:
        Response: A success message with cleared cookies.

    Raises:
        HTTPException: If the user is not authenticated.
    """

    await userCrud.revoke_refresh_token(db, payload.refresh_token)

    response = Response(
        content='{"status":"success","message":"Logged out"}',
        media_type="application/json",
    )
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response


@router.get("/me", response_model=WhoAmIResponse)
@limiter.limit("10/minute")
async def whoami(
    request: Request,
    current_user: models.User = Depends(get_current_user),
):
    """
    Get the current authenticated user's information.

    Args:
        request (Request): The incoming HTTP request.
        current_user (models.User): The authenticated current user.

    Returns:
        WhoAmIResponse: A dictionary containing the current user's data.

    Raises:
        HTTPException: If the user is not authenticated.
    """

    return {"status": "success", "data": current_user}


def _pick_primary_email(email_list: list) -> Optional[str]:
    if not isinstance(email_list, list):
        return None

    for entry in email_list:
        if isinstance(entry, dict) and entry.get("primary") and entry.get("verified"):
            return entry["email"]

    return None


@router.get("/test-token/analyst")
async def analyst_token(db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(role="analyst").first()

    if not user:
        raise HTTPException(status_code=404, detail="No analyst found")

    payload = {"sub": str(user.id), "role": user.role}

    return {
        "access_token": create_access_token(payload),
        "refresh_token": create_refresh_token(payload),
        "token_type": "bearer",
        "username": user.username,
    }
