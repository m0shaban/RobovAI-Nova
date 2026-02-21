"""
🧪 Tests — Health, Pages & System Endpoints
═══════════════════════════════════════════════
Covers: /health, /, /tools, /tools/list, page routes, favicon.
"""

import pytest


class TestHealth:
    """GET /health — should always return 200 with platform info."""

    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_response_shape(self, client):
        data = client.get("/health").json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "tools_count" in data
        assert isinstance(data["tools_count"], int)
        assert "platforms" in data

    def test_health_platforms_list(self, client):
        platforms = client.get("/health").json()["platforms"]
        for p in ["web", "telegram"]:
            assert p in platforms


class TestPages:
    """Static page routes — should return 200 with HTML content."""

    @pytest.mark.parametrize(
        "path",
        ["/", "/chat", "/developers", "/login", "/signup", "/admin",
         "/settings", "/chatbot-builder", "/smart-agents"],
    )
    def test_page_returns_200(self, client, path):
        resp = client.get(path)
        assert resp.status_code == 200
        assert "text/html" in resp.headers.get("content-type", "")

    @pytest.mark.parametrize(
        "page",
        ["chat", "signup", "login", "admin", "account", "settings",
         "developers", "index"],
    )
    def test_html_extension_pages(self, client, page):
        resp = client.get(f"/{page}.html")
        assert resp.status_code == 200

    def test_disallowed_page_returns_404(self, client):
        resp = client.get("/../../etc/passwd.html")
        assert resp.status_code == 404

    def test_path_traversal_blocked(self, client):
        resp = client.get("/..%2F..%2Fetc%2Fpasswd.html")
        assert resp.status_code in (404, 422)


class TestToolsEndpoints:
    """GET /tools and /tools/list — tool registry."""

    def test_tools_returns_200(self, client):
        resp = client.get("/tools")
        assert resp.status_code == 200

    def test_tools_response_shape(self, client):
        data = client.get("/tools").json()
        assert data["status"] == "success"
        assert "tools" in data
        assert "grouped" in data
        assert "count" in data
        assert isinstance(data["count"], int)

    def test_tools_list_alias(self, client):
        """GET /tools/list should return exact same shape as /tools."""
        data = client.get("/tools/list").json()
        assert data["status"] == "success"
        assert "count" in data

    def test_tools_count_positive(self, client):
        count = client.get("/tools").json()["count"]
        assert count > 0, "Tool registry should have at least 1 tool"


class TestFavicon:
    """GET /favicon.ico."""

    def test_favicon_returns_200_or_404(self, client):
        resp = client.get("/favicon.ico")
        assert resp.status_code in (200, 404)


class TestSecurityHeaders:
    """All responses should include security headers."""

    def test_x_content_type_options(self, client):
        resp = client.get("/health")
        assert resp.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options(self, client):
        resp = client.get("/health")
        assert resp.headers.get("x-frame-options") == "DENY"

    def test_referrer_policy(self, client):
        resp = client.get("/health")
        assert "strict-origin" in resp.headers.get("referrer-policy", "")

    def test_xss_protection(self, client):
        resp = client.get("/health")
        assert resp.headers.get("x-xss-protection") == "1; mode=block"
