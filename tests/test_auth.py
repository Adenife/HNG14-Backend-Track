"""
Tests for authentication endpoints and token lifecycle.
"""
import pytest
from app.core.security import create_access_token, create_refresh_token, hash_token


# ---------------------------------------------------------------------------
# Security utilities
# ---------------------------------------------------------------------------
class TestSecurityUtils:
    def test_access_token_created_and_verified(self):
        from app.core.security import verify_token
        token = create_access_token({"sub": "user-123", "role": "analyst"})
        payload = verify_token(token, expected_type="access")
        assert payload["sub"] == "user-123"
        assert payload["role"] == "analyst"

    def test_refresh_token_type_is_enforced(self):
        from app.core.security import verify_token
        from fastapi import HTTPException
        access = create_access_token({"sub": "user-123"})
        with pytest.raises(HTTPException) as exc:
            verify_token(access, expected_type="refresh")
        assert exc.value.status_code == 401

    def test_hash_token_is_deterministic(self):
        raw = "some-token-value"
        assert hash_token(raw) == hash_token(raw)

    def test_pkce_pair_is_valid(self):
        import base64, hashlib
        from app.core.security import generate_pkce_pair
        verifier, challenge = generate_pkce_pair()
        digest = hashlib.sha256(verifier.encode()).digest()
        expected = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
        assert challenge == expected


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------
class TestAuthEndpoints:
    def test_github_redirect(self, client):
        """GET /auth/github should redirect to GitHub."""
        resp = client.get("/auth/github", follow_redirects=False)
        assert resp.status_code in (302, 307)
        assert "github.com/login/oauth/authorize" in resp.headers["location"]

    def test_whoami_requires_auth(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_whoami_returns_user(self, client, admin_token):
        token, user = admin_token
        resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["username"] == "adminuser"
        assert data["data"]["role"] == "admin"

    def test_logout_requires_auth(self, client):
        resp = client.post("/auth/logout", json={"refresh_token": "fake"})
        assert resp.status_code == 401

    def test_refresh_with_invalid_token(self, client):
        resp = client.post("/auth/refresh", json={"refresh_token": "not-a-real-token"})
        assert resp.status_code == 401
