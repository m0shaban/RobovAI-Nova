"""
🧪 Tests — Platform Webhook Endpoints
══════════════════════════════════════════════
Covers: /discord_webhook, /webhooks/status, /whatsapp_webhook, /messenger_webhook
"""

import json
import hmac
import hashlib
from unittest.mock import AsyncMock, patch, MagicMock

import pytest


# ═══════════════════════════════════════════════════════════════════════
# 📊 WEBHOOK STATUS
# ═══════════════════════════════════════════════════════════════════════


class TestWebhookStatus:
    """GET /webhooks/status — platform configuration overview."""

    def test_status_returns_200(self, client):
        """Status endpoint should be publicly accessible."""
        resp = client.get("/webhooks/status")
        assert resp.status_code == 200

    def test_status_response_shape(self, client):
        """Response must include all expected keys."""
        data = client.get("/webhooks/status").json()
        assert data["status"] == "success"
        assert "total_platforms" in data
        assert "configured" in data
        assert "platforms" in data

    def test_status_lists_four_platforms(self, client):
        """All four platforms must be present."""
        data = client.get("/webhooks/status").json()
        platforms = data["platforms"]
        assert set(platforms.keys()) == {"telegram", "whatsapp", "messenger", "discord"}

    def test_status_platform_fields(self, client):
        """Each platform must have configured, endpoint, docs fields."""
        data = client.get("/webhooks/status").json()
        for name, info in data["platforms"].items():
            assert "configured" in info, f"{name} missing 'configured'"
            assert "endpoint" in info, f"{name} missing 'endpoint'"
            assert "docs" in info, f"{name} missing 'docs'"
            assert isinstance(info["configured"], bool)
            assert info["endpoint"].startswith("/")

    def test_status_configured_count_matches(self, client):
        """configured count must equal sum of True values."""
        data = client.get("/webhooks/status").json()
        actual = sum(1 for p in data["platforms"].values() if p["configured"])
        assert data["configured"] == actual

    def test_status_total_equals_four(self, client):
        """Total platforms should be 4."""
        data = client.get("/webhooks/status").json()
        assert data["total_platforms"] == 4


# ═══════════════════════════════════════════════════════════════════════
# 🎮 DISCORD WEBHOOK
# ═══════════════════════════════════════════════════════════════════════


class TestDiscordWebhook:
    """POST /discord_webhook — Discord interactions endpoint."""

    def test_ping_returns_type_1(self, client):
        """Discord ping (type 1) must echo type 1 for verification."""
        resp = client.post(
            "/discord_webhook",
            content=json.dumps({"type": 1}),
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 200
        assert resp.json()["type"] == 1

    def test_slash_command_returns_type_4(self, client):
        """Slash command (type 2) must return a type 4 response."""
        payload = {
            "type": 2,
            "data": {"name": "ask", "options": [{"name": "question", "value": "ping"}]},
            "member": {"user": {"id": "12345", "username": "tester"}},
            "channel_id": "67890",
            "id": "int-001",
            "token": "fake-token",
        }
        with patch(
            "backend.core.smart_router.SmartToolRouter"
        ) as mock_cls:
            mock_cls.route_message = AsyncMock(
                return_value={"type": "llm", "result": None}
            )
            with patch("backend.core.llm.llm_client") as mock_llm:
                mock_llm.generate = AsyncMock(return_value="Hello from Nova!")
                resp = client.post(
                    "/discord_webhook",
                    content=json.dumps(payload),
                    headers={"Content-Type": "application/json"},
                )

        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == 4
        assert "content" in data["data"]

    def test_empty_body_returns_error(self, client):
        """Empty or malformed body should still return a type-4 error response."""
        resp = client.post(
            "/discord_webhook",
            content=b"not json",
            headers={"Content-Type": "application/json"},
        )
        # The endpoint returns type 4 error response on exceptions
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == 4
        assert "error" in data["data"]["content"].lower() or "❌" in data["data"]["content"]

    def test_component_interaction_returns_type_4(self, client):
        """Message component (type 3) should return a response."""
        payload = {
            "type": 3,
            "data": {"custom_id": "button_1"},
            "member": {"user": {"id": "12345", "username": "tester"}},
            "channel_id": "67890",
            "message": {"content": "test"},
        }
        resp = client.post(
            "/discord_webhook",
            content=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["type"] == 4


# ═══════════════════════════════════════════════════════════════════════
# 📱 WHATSAPP WEBHOOK
# ═══════════════════════════════════════════════════════════════════════


class TestWhatsAppWebhook:
    """GET/POST /whatsapp_webhook — WhatsApp Cloud API."""

    def test_verify_token_success(self, client):
        """GET with correct verify token → returns challenge."""
        resp = client.get(
            "/whatsapp_webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "robovai_verify",
                "hub.challenge": "test_challenge_str",
            },
        )
        assert resp.status_code == 200
        assert resp.text == "test_challenge_str"

    def test_verify_token_failure(self, client):
        """GET with wrong verify token → 403."""
        resp = client.get(
            "/whatsapp_webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong_token",
                "hub.challenge": "abc",
            },
        )
        assert resp.status_code == 403

    @patch.dict("os.environ", {"WHATSAPP_APP_SECRET": "test_secret"})
    def test_invalid_signature_returns_403(self, client):
        """POST with invalid HMAC signature → 403."""
        body = json.dumps({"object": "whatsapp_business_account", "entry": []})
        resp = client.post(
            "/whatsapp_webhook",
            content=body.encode(),
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": "sha256=invalid_hmac",
            },
        )
        assert resp.status_code == 403

    @patch.dict("os.environ", {"WHATSAPP_APP_SECRET": "test_secret"})
    def test_valid_signature_accepted(self, client):
        """POST with valid HMAC signature → processes payload."""
        body = json.dumps({"object": "whatsapp_business_account", "entry": []}).encode()
        mac = hmac.new(b"test_secret", body, hashlib.sha256).hexdigest()

        resp = client.post(
            "/whatsapp_webhook",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": f"sha256={mac}",
            },
        )
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════
# 💬 MESSENGER WEBHOOK
# ═══════════════════════════════════════════════════════════════════════


class TestMessengerWebhook:
    """GET/POST /messenger_webhook — Facebook Messenger."""

    def test_verify_token_success(self, client):
        """GET with correct verify token → returns challenge."""
        resp = client.get(
            "/messenger_webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "robovai_verify",
                "hub.challenge": "messenger_challenge",
            },
        )
        assert resp.status_code == 200

    def test_verify_token_failure(self, client):
        """GET with wrong verify token → 403."""
        resp = client.get(
            "/messenger_webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "bad_token",
                "hub.challenge": "abc",
            },
        )
        assert resp.status_code == 403

    @patch.dict("os.environ", {"MESSENGER_APP_SECRET": "msg_secret"})
    def test_invalid_signature_returns_403(self, client):
        """POST with invalid HMAC signature → 403."""
        body = json.dumps({"object": "page", "entry": []})
        resp = client.post(
            "/messenger_webhook",
            content=body.encode(),
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": "sha256=badvalue",
            },
        )
        assert resp.status_code == 403

    @patch.dict("os.environ", {"MESSENGER_APP_SECRET": "msg_secret"})
    def test_valid_signature_accepted(self, client):
        """POST with valid HMAC signature → processes payload."""
        body = json.dumps({"object": "page", "entry": []}).encode()
        mac = hmac.new(b"msg_secret", body, hashlib.sha256).hexdigest()

        resp = client.post(
            "/messenger_webhook",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": f"sha256={mac}",
            },
        )
        assert resp.status_code == 200
