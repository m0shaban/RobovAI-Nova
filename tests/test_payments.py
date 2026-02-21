"""
🧪 Tests — Payments & Pricing Endpoints
══════════════════════════════════════════
Covers: /payments/pricing, /payments/subscription, /payments/checkout
"""

import pytest
from unittest.mock import AsyncMock


class TestPaymentsPricing:
    """GET /payments/pricing — public pricing info."""

    def test_pricing_returns_200(self, client):
        resp = client.get("/payments/pricing")
        assert resp.status_code == 200


class TestPaymentsSubscription:
    """GET /payments/subscription — requires auth."""

    def test_subscription_returns_user_tier(self, client, auth_headers):
        resp = client.get("/payments/subscription", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "tier" in data
        assert "balance" in data
        assert "can_use" in data

    def test_subscription_requires_auth(self, client):
        """No auth → 401 from OAuth2 scheme."""
        resp = client.get("/payments/subscription")
        assert resp.status_code == 401


class TestPaymentsCheckout:
    """POST /payments/checkout — requires auth + valid plan."""

    def test_checkout_requires_auth(self, client):
        """No auth → 401 from OAuth2 scheme."""
        resp = client.post("/payments/checkout?plan=pro")
        assert resp.status_code == 401

    def test_checkout_invalid_plan(self, client, auth_headers):
        """Invalid plan name → 400."""
        resp = client.post(
            "/payments/checkout?plan=nonexistent",
            headers=auth_headers,
        )
        assert resp.status_code == 400
