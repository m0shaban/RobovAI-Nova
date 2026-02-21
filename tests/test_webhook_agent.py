"""
🧪 Tests — Webhook & Agent Endpoints
══════════════════════════════════════════
Covers: /webhook (main chat), /agent/run, /user/balance, /user/usage-history
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestWebhook:
    """POST /webhook — central chat entry point."""

    def test_webhook_requires_auth_for_web(self, client):
        """Web-platform webhook without auth → 401 from OAuth2 scheme."""
        resp = client.post(
            "/webhook",
            json={
                "user_id": "user_1",
                "message": "hello",
                "platform": "web",
            },
        )
        assert resp.status_code == 401

    def test_webhook_accepts_valid_payload(self, client, auth_headers):
        """With valid auth, webhook should process and return a response."""
        mock_routing = {
            "type": "tool",
            "result": {"output": "Hello! How can I help?"},
            "tool_name": "test_tool",
        }
        with patch(
            "backend.core.smart_router.SmartToolRouter"
        ) as mock_cls:
            mock_cls.route_message = AsyncMock(return_value=mock_routing)
            resp = client.post(
                "/webhook",
                json={
                    "user_id": "1",
                    "message": "Hello",
                    "platform": "web",
                },
                headers=auth_headers,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "success"
            assert "response" in data

    def test_webhook_missing_fields(self, client, auth_headers):
        """Missing required fields → 422 Pydantic validation."""
        resp = client.post(
            "/webhook",
            json={"user_id": "1"},
            headers=auth_headers,
        )
        assert resp.status_code == 422


class TestUserEndpoints:
    """GET /user/balance, /user/usage-history — require auth."""

    def test_balance_returns_200(self, client, auth_headers):
        resp = client.get("/user/balance", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "balance" in data
        assert "daily_used" in data
        assert "tier" in data

    def test_balance_requires_auth(self, client):
        """No auth → 401 from OAuth2 scheme."""
        resp = client.get("/user/balance")
        assert resp.status_code == 401

    def test_usage_history(self, client, auth_headers):
        resp = client.get("/user/usage-history", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert isinstance(data["history"], list)


class TestAgentRun:
    """POST /agent/run — AI agent execution."""

    def test_agent_run_success(self, client, auth_headers):
        """Agent endpoint should accept the AgentRequest schema and return result."""
        mock_result = {
            "success": True,
            "final_answer": "The weather in Cairo is sunny.",
            "tool_results": [],
            "plan": [],
            "phase": "done",
            "errors": [],
        }
        with patch(
            "backend.agent.graph.run_agent",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = client.post(
                "/agent/run",
                json={
                    "message": "What is the weather in Cairo?",
                    "user_id": "1",
                    "platform": "web",
                    "use_agent": True,
                },
                headers=auth_headers,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "success"
            assert "response" in data

    def test_agent_run_missing_message(self, client, auth_headers):
        """Missing message field → 422."""
        resp = client.post(
            "/agent/run",
            json={"user_id": "1"},
            headers=auth_headers,
        )
        assert resp.status_code == 422
