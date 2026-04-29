"""
Tests for profile endpoints: auth guards, RBAC, versioning, pagination links, CSV export.
"""
import pytest


HEADERS_V1 = {"X-API-Version": "1"}


class TestAPIVersioning:
    def test_missing_version_header_returns_400(self, client, analyst_token):
        token, _ = analyst_token
        resp = client.get(
            "/api/profiles",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400
        assert resp.json()["message"] == "API version header required"

    def test_wrong_version_header_returns_400(self, client, analyst_token):
        token, _ = analyst_token
        resp = client.get(
            "/api/profiles",
            headers={"Authorization": f"Bearer {token}", "X-API-Version": "2"},
        )
        assert resp.status_code == 400

    def test_correct_version_header_passes(self, client, analyst_token):
        token, _ = analyst_token
        resp = client.get(
            "/api/profiles",
            headers={"Authorization": f"Bearer {token}", **HEADERS_V1},
        )
        assert resp.status_code == 200


class TestProfileAuth:
    def test_list_profiles_requires_auth(self, client):
        resp = client.get("/api/profiles", headers=HEADERS_V1)
        assert resp.status_code == 401

    def test_get_profile_requires_auth(self, client):
        import uuid
        resp = client.get(f"/api/profiles/{uuid.uuid4()}", headers=HEADERS_V1)
        assert resp.status_code == 401

    def test_create_profile_requires_admin(self, client, analyst_token):
        token, _ = analyst_token
        resp = client.post(
            "/api/profiles",
            json={"name": "Test"},
            headers={"Authorization": f"Bearer {token}", **HEADERS_V1},
        )
        assert resp.status_code == 403
        assert "Admin" in resp.json()["message"]

    def test_delete_profile_requires_admin(self, client, analyst_token):
        import uuid
        token, _ = analyst_token
        resp = client.delete(
            f"/api/profiles/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}", **HEADERS_V1},
        )
        assert resp.status_code == 403

    def test_inactive_user_is_forbidden(self, client, db_session):
        from app.models.models import User
        from app.core.security import create_access_token
        from uuid6 import uuid7

        user = User(
            id=uuid7(),
            github_id="inactive-github-id",
            username="inactiveuser",
            role="analyst",
            is_active=False,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        token = create_access_token({"sub": str(user.id), "role": "analyst"})
        resp = client.get(
            "/api/profiles",
            headers={"Authorization": f"Bearer {token}", **HEADERS_V1},
        )
        assert resp.status_code == 403


class TestPaginationLinks:
    def test_list_profiles_includes_links(self, client, analyst_token):
        token, _ = analyst_token
        resp = client.get(
            "/api/profiles?page=1&limit=10",
            headers={"Authorization": f"Bearer {token}", **HEADERS_V1},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "links" in body
        assert "self" in body["links"]
        assert "total_pages" in body

    def test_first_page_has_no_prev(self, client, analyst_token):
        token, _ = analyst_token
        resp = client.get(
            "/api/profiles?page=1&limit=10",
            headers={"Authorization": f"Bearer {token}", **HEADERS_V1},
        )
        body = resp.json()
        assert body["links"]["prev"] is None


class TestCSVExport:
    def test_export_requires_auth(self, client):
        resp = client.get("/api/profiles/export?format=csv", headers=HEADERS_V1)
        assert resp.status_code == 401

    def test_export_returns_csv(self, client, analyst_token):
        token, _ = analyst_token
        resp = client.get(
            "/api/profiles/export?format=csv",
            headers={"Authorization": f"Bearer {token}", **HEADERS_V1},
        )
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]
        assert "attachment" in resp.headers.get("content-disposition", "")

    def test_export_invalid_format(self, client, analyst_token):
        token, _ = analyst_token
        resp = client.get(
            "/api/profiles/export?format=json",
            headers={"Authorization": f"Bearer {token}", **HEADERS_V1},
        )
        assert resp.status_code == 400
