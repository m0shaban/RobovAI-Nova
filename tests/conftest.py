"""
🧪 Pytest Configuration — RobovAI Nova
═══════════════════════════════════════════
Shared fixtures: test client, mock auth, mock DB.
"""

import os
import sys
from typing import AsyncGenerator, Dict, Any
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import pytest_asyncio

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Set test env vars BEFORE importing the app
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-pytest-" + "x" * 40)
os.environ.setdefault("DATABASE_PATH", ":memory:")
os.environ.setdefault("ENVIRONMENT", "test")

# ── Pre-mock heavy/optional deps that may not be installed locally ──
_OPTIONAL_MODULES = [
    "langchain_qdrant",
    "qdrant_client",
    "qdrant_client.http",
    "qdrant_client.http.models",
]
for _mod in _OPTIONAL_MODULES:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()


# ── Lazy app import (after env setup) ──────────────────────────
@pytest.fixture(scope="session")
def app():
    """Import and return the FastAPI app."""
    from backend.main import app as _app
    return _app


@pytest.fixture()
def client(app):
    """Synchronous TestClient for non-async tests."""
    from fastapi.testclient import TestClient
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest_asyncio.fixture()
async def async_client(app):
    """Async TestClient using httpx for async tests."""
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Mock user fixtures ─────────────────────────────────────────
MOCK_USER: Dict[str, Any] = {
    "id": 1,
    "email": "test@robovai.com",
    "full_name": "Test User",
    "role": "user",
    "is_verified": True,
    "balance": 100,
}

MOCK_ADMIN: Dict[str, Any] = {
    "id": 99,
    "email": "admin@robovai.com",
    "full_name": "Admin User",
    "role": "admin",
    "is_verified": True,
    "balance": 9999,
}


@pytest.fixture()
def auth_headers() -> Dict[str, str]:
    """Return Authorization header with a valid test JWT."""
    from backend.core.security import create_access_token
    token = create_access_token(data={"sub": MOCK_USER["email"]})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_auth_headers() -> Dict[str, str]:
    """Return Authorization header for admin user."""
    from backend.core.security import create_access_token
    token = create_access_token(data={"sub": MOCK_ADMIN["email"]})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def _mock_db_session():
    """
    Auto-mock database calls so tests never touch a real DB.
    Patches methods directly on the singleton db_client instance
    so the mocks are visible to every module that imported it.
    """
    from backend.core.database import db_client

    async def _fake_get_session(token: str):
        return {"token": token, "user_id": 1, "expires_at": "2099-01-01T00:00:00"}

    async def _fake_get_user_by_email(email: str):
        if email == MOCK_ADMIN["email"]:
            return MOCK_ADMIN
        return MOCK_USER

    async def _fake_get_daily_usage(user_id: str):
        return {
            "balance": 100,
            "daily_used": 5,
            "daily_limit": 50,
            "tier": "free",
            "can_use": True,
        }

    async def _fake_get_usage_history(user_id: str):
        return [
            {"date": "2026-02-22", "tool": "weather", "cost": 1},
        ]

    _patches = [
        # ── Auth / session ──
        patch.object(db_client, "get_session", AsyncMock(side_effect=_fake_get_session)),
        patch.object(db_client, "get_user_by_email", AsyncMock(side_effect=_fake_get_user_by_email)),
        patch.object(db_client, "create_user", AsyncMock(return_value={"id": 2, "email": "new@test.com"})),
        patch.object(db_client, "authenticate_user", AsyncMock(return_value=MOCK_USER)),
        patch.object(db_client, "create_session", AsyncMock(return_value=True)),
        patch.object(db_client, "delete_session", AsyncMock(return_value=True)),
        patch.object(db_client, "store_otp", AsyncMock(return_value=True)),
        patch.object(db_client, "cleanup_expired_sessions", AsyncMock()),
        patch.object(db_client, "cleanup_expired_otps", AsyncMock(return_value=0)),
        # ── Usage / balance ──
        patch.object(db_client, "get_daily_usage", AsyncMock(side_effect=_fake_get_daily_usage)),
        patch.object(db_client, "get_usage_history", AsyncMock(side_effect=_fake_get_usage_history)),
        # ── Chat / messages ──
        patch.object(db_client, "save_message", AsyncMock(return_value=True)),
        patch.object(db_client, "get_recent_messages", AsyncMock(return_value=[])),
        # ── Admin ──
        patch.object(db_client, "get_stats", AsyncMock(return_value={
            "total_users": 10, "active_today": 3, "total_messages": 500,
        })),
        patch.object(db_client, "get_all_users", AsyncMock(return_value=[MOCK_USER, MOCK_ADMIN])),
        patch.object(db_client, "update_user_role", AsyncMock(return_value=True)),
        patch.object(db_client, "add_tokens", AsyncMock(return_value=True)),
        patch.object(db_client, "get_admin_analytics", AsyncMock(return_value={
            "daily_messages": [], "top_tools": [], "user_growth": [],
        })),
    ]

    for p in _patches:
        p.start()
    yield db_client
    for p in _patches:
        p.stop()
