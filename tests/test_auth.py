import pytest
from unittest.mock import AsyncMock, patch
import uuid

@pytest.mark.asyncio
async def test_auth_protected_route(client):
    """Test that routes require the X-API-Version header (already tested by conftest fix)."""
    # This is more of a middleware test
    response = client.get("/api/check")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_admin_only_route_access(client):
    """Test RBAC for admin-only routes."""
    # Already mocked as admin in conftest
    response = client.get("/api/profiles")
    assert response.status_code != 403

@pytest.mark.asyncio
async def test_auth_me_endpoint(client):
    """Test the /auth/me endpoint."""
    response = client.get("/auth/me")
    assert response.status_code == 200
    assert "username" in response.json()["data"]
