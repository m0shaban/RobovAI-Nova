"""
🧪 Tests — Admin Endpoints
════════════════════════════════
Covers: /admin/stats, /admin/users, /admin/tools, /admin/set-role, /admin/add-tokens
All require admin role.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestAdminStats:
    """GET /admin/stats — admin dashboard data."""

    def test_admin_stats_requires_auth(self, client):
        """No auth → 401 from OAuth2 scheme."""
        resp = client.get("/admin/stats")
        assert resp.status_code == 401

    def test_admin_stats_forbidden_for_user(self, client, auth_headers):
        """Regular user (role=user) should get 403."""
        resp = client.get("/admin/stats", headers=auth_headers)
        assert resp.status_code == 403

    def test_admin_stats_allowed_for_admin(self, client, admin_auth_headers):
        """Admin user should get 200."""
        resp = client.get("/admin/stats", headers=admin_auth_headers)
        assert resp.status_code == 200


class TestAdminUsers:
    """GET /admin/users — list all users."""

    def test_admin_users_forbidden_for_user(self, client, auth_headers):
        resp = client.get("/admin/users", headers=auth_headers)
        assert resp.status_code == 403

    def test_admin_users_allowed_for_admin(self, client, admin_auth_headers):
        resp = client.get("/admin/users", headers=admin_auth_headers)
        assert resp.status_code == 200


class TestAdminTools:
    """GET /admin/tools — tool registry stats."""

    def test_admin_tools_forbidden_for_user(self, client, auth_headers):
        resp = client.get("/admin/tools", headers=auth_headers)
        assert resp.status_code == 403

    def test_admin_tools_allowed_for_admin(self, client, admin_auth_headers):
        mock_tool = MagicMock()
        mock_tool.description = "Test tool"
        mock_tool.category = "utility"
        with patch("backend.main.ToolRegistry") as mock_reg:
            mock_reg.list_tools.return_value = ["/test"]
            mock_reg.get_tool.return_value = mock_tool
            resp = client.get("/admin/tools", headers=admin_auth_headers)
        assert resp.status_code == 200


class TestAdminSetRole:
    """POST /admin/set-role — change user role."""

    def test_set_role_forbidden_for_user(self, client, auth_headers):
        resp = client.post(
            "/admin/set-role",
            json={"user_id": 1, "role": "admin"},
            headers=auth_headers,
        )
        assert resp.status_code == 403

    def test_set_role_requires_body(self, client, admin_auth_headers):
        resp = client.post("/admin/set-role", json={}, headers=admin_auth_headers)
        assert resp.status_code == 422


class TestAdminAddTokens:
    """POST /admin/add-tokens — add tokens to a user."""

    def test_add_tokens_forbidden_for_user(self, client, auth_headers):
        resp = client.post(
            "/admin/add-tokens",
            json={"user_id": 1, "amount": 100},
            headers=auth_headers,
        )
        assert resp.status_code == 403

    def test_add_tokens_requires_body(self, client, admin_auth_headers):
        resp = client.post("/admin/add-tokens", json={}, headers=admin_auth_headers)
        assert resp.status_code == 422
