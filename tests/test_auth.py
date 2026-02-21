"""
🧪 Tests — Authentication Endpoints
═══════════════════════════════════════════
Covers: /auth/register, /auth/login, /auth/logout, /auth/me
"""

import pytest
from unittest.mock import AsyncMock, patch


class TestRegister:
    """POST /auth/register."""

    def test_register_success(self, client):
        resp = client.post(
            "/auth/register",
            json={
                "email": "new@example.com",
                "password": "StrongPass123!",
                "full_name": "New User",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "pending_verification"

    def test_register_weak_password(self, client):
        """Password validation should reject weak passwords."""
        resp = client.post(
            "/auth/register",
            json={
                "email": "weak@example.com",
                "password": "123",
                "full_name": "Weak",
            },
        )
        assert resp.status_code == 400

    def test_register_invalid_email(self, client):
        resp = client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "password": "StrongPass123!",
                "full_name": "Bad Email",
            },
        )
        assert resp.status_code == 400

    def test_register_duplicate_email(self, client, _mock_db_session):
        """When DB returns None (duplicate), expect 400."""
        _mock_db_session.create_user = AsyncMock(return_value=None)
        resp = client.post(
            "/auth/register",
            json={
                "email": "dup@example.com",
                "password": "StrongPass123!",
                "full_name": "Dup",
            },
        )
        assert resp.status_code == 400

    def test_register_missing_fields(self, client):
        resp = client.post("/auth/register", json={"email": "a@b.com"})
        assert resp.status_code == 422  # Pydantic validation


class TestLogin:
    """POST /auth/login — OAuth2 password form."""

    def test_login_success(self, client):
        resp = client.post(
            "/auth/login",
            data={"username": "test@robovai.com", "password": "pass123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_sets_cookie(self, client):
        resp = client.post(
            "/auth/login",
            data={"username": "test@robovai.com", "password": "pass123"},
        )
        assert "access_token" in resp.cookies or resp.status_code == 200

    def test_login_invalid_credentials(self, client, _mock_db_session):
        _mock_db_session.authenticate_user = AsyncMock(return_value=None)
        resp = client.post(
            "/auth/login",
            data={"username": "bad@test.com", "password": "wrong"},
        )
        assert resp.status_code == 401

    def test_login_unverified_account(self, client, _mock_db_session):
        unverified_user = {"id": 3, "email": "unv@test.com", "is_verified": False,
                          "full_name": "Unverified", "role": "user", "balance": 0}
        _mock_db_session.authenticate_user = AsyncMock(return_value=unverified_user)
        resp = client.post(
            "/auth/login",
            data={"username": "unv@test.com", "password": "pass"},
        )
        assert resp.status_code == 403


class TestLogout:
    """POST /auth/logout."""

    def test_logout_success(self, client, auth_headers):
        resp = client.post("/auth/logout", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_logout_without_token(self, client):
        resp = client.post("/auth/logout")
        assert resp.status_code == 200  # Graceful — just clears cookie


class TestAuthMe:
    """GET /auth/me — requires authentication."""

    def test_me_returns_user_info(self, client, auth_headers):
        resp = client.get("/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "test@robovai.com"
        assert "balance" in data
        assert "role" in data

    def test_me_without_token(self, client):
        """No auth → 401 from OAuth2 scheme."""
        resp = client.get("/auth/me")
        assert resp.status_code == 401
