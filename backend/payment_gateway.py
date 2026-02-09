"""
💳 RobovAI Nova — Unified Payment Gateway
═══════════════════════════════════════════
Supports: Stripe · Paymob · LemonSqueezy
Auto-detects which provider is configured.

Setup:
  Stripe  → STRIPE_SECRET_KEY + STRIPE_WEBHOOK_SECRET
  Paymob  → PAYMOB_API_KEY + PAYMOB_INTEGRATION_IDS
  Lemon   → LEMONSQUEEZY_API_KEY + LEMONSQUEEZY_STORE_ID
"""

import os
import hmac
import hashlib
import json
import logging
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

logger = logging.getLogger("robovai.payments")

# ═══════════════════════════════════════════════════════════════
# 📦 PLANS & PRICING
# ═══════════════════════════════════════════════════════════════

PLANS = {
    "free": {
        "name_ar": "مجاني",
        "name_en": "Free",
        "price_usd": 0,
        "price_egp": 0,
        "tokens": 100,
        "daily_limit": 50,
        "features_ar": ["112 أداة ذكية", "50 طلب/يوم", "100 توكن مجاني"],
        "features_en": ["112 AI Tools", "50 requests/day", "100 free tokens"],
    },
    "pro": {
        "name_ar": "احترافي",
        "name_en": "Pro",
        "price_usd": 9.99,
        "price_egp": 299,
        "tokens": 2000,
        "daily_limit": 500,
        "features_ar": [
            "كل الأدوات",
            "500 طلب/يوم",
            "2000 توكن/شهر",
            "دعم أولوية",
            "بدون إعلانات",
        ],
        "features_en": [
            "All tools",
            "500 requests/day",
            "2000 tokens/month",
            "Priority support",
            "No ads",
        ],
    },
    "enterprise": {
        "name_ar": "مؤسسات",
        "name_en": "Enterprise",
        "price_usd": 49.99,
        "price_egp": 1499,
        "tokens": -1,  # unlimited
        "daily_limit": -1,
        "features_ar": [
            "طلبات غير محدودة",
            "توكنز غير محدودة",
            "دعم مخصص 24/7",
            "API Access",
            "Whitelabel",
        ],
        "features_en": [
            "Unlimited requests",
            "Unlimited tokens",
            "24/7 Dedicated support",
            "API Access",
            "Whitelabel",
        ],
    },
}

# Token top-up packages (one-time purchase)
TOKEN_PACKAGES = {
    "tokens_500": {"tokens": 500, "price_usd": 4.99, "price_egp": 149},
    "tokens_2000": {"tokens": 2000, "price_usd": 14.99, "price_egp": 449},
    "tokens_5000": {"tokens": 5000, "price_usd": 29.99, "price_egp": 899},
}


# ═══════════════════════════════════════════════════════════════
# 🔧 CONFIG — Auto-detect from env vars
# ═══════════════════════════════════════════════════════════════

# Stripe
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRO_PRICE_ID = os.getenv("STRIPE_PRO_PRICE_ID", "")
STRIPE_ENTERPRISE_PRICE_ID = os.getenv("STRIPE_ENTERPRISE_PRICE_ID", "")

# Paymob (Egypt / MENA)
PAYMOB_API_KEY = os.getenv("PAYMOB_API_KEY", "")
PAYMOB_INTEGRATION_ID = os.getenv("PAYMOB_INTEGRATION_ID", "")  # card
PAYMOB_WALLET_INTEGRATION_ID = os.getenv("PAYMOB_WALLET_INTEGRATION_ID", "")  # mobile wallet
PAYMOB_IFRAME_ID = os.getenv("PAYMOB_IFRAME_ID", "")
PAYMOB_HMAC_SECRET = os.getenv("PAYMOB_HMAC_SECRET", "")

# LemonSqueezy
LEMONSQUEEZY_API_KEY = os.getenv("LEMONSQUEEZY_API_KEY", "")
LEMONSQUEEZY_STORE_ID = os.getenv("LEMONSQUEEZY_STORE_ID", "")
LEMONSQUEEZY_WEBHOOK_SECRET = os.getenv("LEMONSQUEEZY_WEBHOOK_SECRET", "")
LEMON_PRO_VARIANT = os.getenv("LEMONSQUEEZY_PRO_VARIANT_ID", "")
LEMON_ENTERPRISE_VARIANT = os.getenv("LEMONSQUEEZY_ENTERPRISE_VARIANT_ID", "")

# App URL (for redirects)
APP_URL = os.getenv("EXTERNAL_URL", os.getenv("APP_URL", "http://localhost:8000"))


def get_active_providers() -> List[str]:
    """Return list of configured payment providers."""
    providers = []
    if STRIPE_SECRET_KEY:
        providers.append("stripe")
    if PAYMOB_API_KEY:
        providers.append("paymob")
    if LEMONSQUEEZY_API_KEY:
        providers.append("lemonsqueezy")
    return providers


# ═══════════════════════════════════════════════════════════════
# 💳 STRIPE
# ═══════════════════════════════════════════════════════════════

class StripeProvider:
    """Stripe payment provider (International / Cards)."""

    API_BASE = "https://api.stripe.com/v1"

    @staticmethod
    def _headers():
        return {"Authorization": f"Bearer {STRIPE_SECRET_KEY}"}

    @classmethod
    async def create_checkout(
        cls,
        user_id: str,
        user_email: str,
        plan: str = "pro",
        is_token_package: bool = False,
        package_id: str = "",
    ) -> Optional[str]:
        """Create Stripe Checkout Session → returns URL."""
        if not STRIPE_SECRET_KEY:
            return None

        async with httpx.AsyncClient() as client:
            try:
                params = {
                    "success_url": f"{APP_URL}/chat?payment=success&session_id={{CHECKOUT_SESSION_ID}}",
                    "cancel_url": f"{APP_URL}/settings?payment=cancelled",
                    "customer_email": user_email,
                    "metadata[user_id]": user_id,
                    "metadata[plan]": plan,
                }

                if is_token_package and package_id in TOKEN_PACKAGES:
                    pkg = TOKEN_PACKAGES[package_id]
                    params.update({
                        "mode": "payment",
                        "line_items[0][price_data][currency]": "usd",
                        "line_items[0][price_data][product_data][name]": f"RobovAI Tokens ({pkg['tokens']})",
                        "line_items[0][price_data][unit_amount]": int(pkg["price_usd"] * 100),
                        "line_items[0][quantity]": "1",
                        "metadata[type]": "tokens",
                        "metadata[tokens]": str(pkg["tokens"]),
                        "metadata[package_id]": package_id,
                    })
                else:
                    # Subscription
                    price_id = STRIPE_PRO_PRICE_ID if plan == "pro" else STRIPE_ENTERPRISE_PRICE_ID
                    if not price_id:
                        logger.warning(f"Stripe price ID not set for plan: {plan}")
                        return None
                    params.update({
                        "mode": "subscription",
                        "line_items[0][price]": price_id,
                        "line_items[0][quantity]": "1",
                        "metadata[type]": "subscription",
                    })

                resp = await client.post(
                    f"{cls.API_BASE}/checkout/sessions",
                    headers=cls._headers(),
                    data=params,
                )
                if resp.status_code == 200:
                    return resp.json().get("url")
                logger.error(f"Stripe checkout error: {resp.status_code} {resp.text}")
            except Exception as e:
                logger.error(f"Stripe error: {e}")
        return None

    @staticmethod
    def verify_webhook(payload: bytes, sig_header: str) -> Optional[Dict]:
        """Verify Stripe webhook signature and return event data."""
        if not STRIPE_WEBHOOK_SECRET:
            return None
        try:
            import stripe
            stripe.api_key = STRIPE_SECRET_KEY
            event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
            return event
        except ImportError:
            # Manual verification without stripe library
            parts = dict(item.split("=", 1) for item in sig_header.split(",") if "=" in item)
            timestamp = parts.get("t", "")
            v1 = parts.get("v1", "")
            signed_payload = f"{timestamp}.{payload.decode()}"
            expected = hmac.new(
                STRIPE_WEBHOOK_SECRET.encode(), signed_payload.encode(), hashlib.sha256
            ).hexdigest()
            if hmac.compare_digest(expected, v1):
                return json.loads(payload)
        except Exception as e:
            logger.error(f"Stripe webhook verification failed: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# 🇪🇬 PAYMOB (Egypt / MENA — Card + Mobile Wallet)
# ═══════════════════════════════════════════════════════════════

class PaymobProvider:
    """Paymob payment provider (Egypt/MENA — Visa, Mastercard, Fawry, Wallets)."""

    API_BASE = "https://accept.paymob.com/api"

    @classmethod
    async def _get_auth_token(cls) -> Optional[str]:
        """Step 1: Authenticate and get token."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{cls.API_BASE}/auth/tokens",
                json={"api_key": PAYMOB_API_KEY},
            )
            if resp.status_code == 201:
                return resp.json().get("token")
        return None

    @classmethod
    async def _create_order(cls, auth_token: str, amount_cents: int, user_id: str, plan: str) -> Optional[int]:
        """Step 2: Register an order."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{cls.API_BASE}/ecommerce/orders",
                json={
                    "auth_token": auth_token,
                    "delivery_needed": "false",
                    "amount_cents": str(amount_cents),
                    "currency": "EGP",
                    "merchant_order_id": f"robovai_{user_id}_{plan}_{int(datetime.now().timestamp())}",
                    "items": [
                        {
                            "name": f"RobovAI {plan.upper()} Plan",
                            "amount_cents": str(amount_cents),
                            "quantity": "1",
                        }
                    ],
                },
            )
            if resp.status_code in (200, 201):
                return resp.json().get("id")
        return None

    @classmethod
    async def _get_payment_key(
        cls,
        auth_token: str,
        order_id: int,
        amount_cents: int,
        user_email: str,
        user_name: str,
        integration_id: str,
        user_id: str,
        plan: str,
    ) -> Optional[str]:
        """Step 3: Get payment key."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{cls.API_BASE}/acceptance/payment_keys",
                json={
                    "auth_token": auth_token,
                    "amount_cents": str(amount_cents),
                    "expiration": 3600,
                    "order_id": str(order_id),
                    "billing_data": {
                        "email": user_email,
                        "first_name": user_name.split()[0] if user_name else "User",
                        "last_name": user_name.split()[-1] if user_name and len(user_name.split()) > 1 else "NA",
                        "phone_number": "NA",
                        "apartment": "NA",
                        "floor": "NA",
                        "street": "NA",
                        "building": "NA",
                        "shipping_method": "NA",
                        "postal_code": "NA",
                        "city": "Cairo",
                        "country": "EG",
                        "state": "Cairo",
                    },
                    "currency": "EGP",
                    "integration_id": int(integration_id),
                    "lock_order_when_paid": "true",
                    "extra": {
                        "user_id": user_id,
                        "plan": plan,
                    },
                },
            )
            if resp.status_code in (200, 201):
                return resp.json().get("token")
        return None

    @classmethod
    async def create_checkout(
        cls,
        user_id: str,
        user_email: str,
        user_name: str = "",
        plan: str = "pro",
        method: str = "card",  # "card" or "wallet"
        is_token_package: bool = False,
        package_id: str = "",
    ) -> Optional[str]:
        """Full Paymob checkout flow → returns iframe/redirect URL."""
        if not PAYMOB_API_KEY:
            return None

        try:
            # Calculate amount in EGP piasters (cents)
            if is_token_package and package_id in TOKEN_PACKAGES:
                amount_cents = int(TOKEN_PACKAGES[package_id]["price_egp"] * 100)
            else:
                plan_info = PLANS.get(plan)
                if not plan_info or plan_info["price_egp"] == 0:
                    return None
                amount_cents = int(plan_info["price_egp"] * 100)

            # Step 1: Auth
            auth_token = await cls._get_auth_token()
            if not auth_token:
                logger.error("Paymob auth failed")
                return None

            # Step 2: Order
            order_id = await cls._create_order(auth_token, amount_cents, user_id, plan)
            if not order_id:
                logger.error("Paymob order creation failed")
                return None

            # Step 3: Payment Key
            integration_id = PAYMOB_WALLET_INTEGRATION_ID if method == "wallet" else PAYMOB_INTEGRATION_ID
            if not integration_id:
                logger.error(f"Paymob integration ID not set for method: {method}")
                return None

            payment_key = await cls._get_payment_key(
                auth_token, order_id, amount_cents, user_email, user_name or "User",
                integration_id, user_id, plan,
            )
            if not payment_key:
                logger.error("Paymob payment key failed")
                return None

            # Return iframe URL for card, or wallet redirect
            if method == "wallet" and PAYMOB_WALLET_INTEGRATION_ID:
                return f"https://accept.paymob.com/api/acceptance/payments/pay?payment_token={payment_key}"
            elif PAYMOB_IFRAME_ID:
                return f"https://accept.paymob.com/api/acceptance/iframes/{PAYMOB_IFRAME_ID}?payment_token={payment_key}"
            else:
                return f"https://accept.paymob.com/api/acceptance/payments/pay?payment_token={payment_key}"

        except Exception as e:
            logger.error(f"Paymob error: {e}")
        return None

    @staticmethod
    def verify_webhook(data: Dict, hmac_received: str) -> bool:
        """Verify Paymob HMAC callback."""
        if not PAYMOB_HMAC_SECRET:
            return False

        # Paymob requires sorting specific fields
        hmac_fields = [
            "amount_cents", "created_at", "currency", "error_occured",
            "has_parent_transaction", "id", "integration_id",
            "is_3d_secure", "is_auth", "is_capture", "is_refunded",
            "is_standalone_payment", "is_voided", "order",
            "owner", "pending", "source_data_pan",
            "source_data_sub_type", "source_data_type", "success",
        ]

        obj = data.get("obj", data)
        concat = ""
        for field in hmac_fields:
            val = obj.get(field, "")
            if isinstance(val, bool):
                val = str(val).lower()
            elif isinstance(val, dict):
                val = str(val.get("id", ""))
            concat += str(val)

        expected = hmac.new(
            PAYMOB_HMAC_SECRET.encode(), concat.encode(), hashlib.sha512
        ).hexdigest()

        return hmac.compare_digest(expected, hmac_received)


# ═══════════════════════════════════════════════════════════════
# 🍋 LEMONSQUEEZY (Already implemented — kept for compatibility)
# ═══════════════════════════════════════════════════════════════

class LemonSqueezyProvider:
    """LemonSqueezy payment provider."""

    API_BASE = "https://api.lemonsqueezy.com/v1"

    @staticmethod
    def _headers():
        return {
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
            "Authorization": f"Bearer {LEMONSQUEEZY_API_KEY}",
        }

    @classmethod
    async def create_checkout(
        cls,
        user_id: str,
        user_email: str,
        plan: str = "pro",
    ) -> Optional[str]:
        if not LEMONSQUEEZY_API_KEY:
            return None

        variant_id = LEMON_PRO_VARIANT if plan == "pro" else LEMON_ENTERPRISE_VARIANT
        if not variant_id:
            return None

        payload = {
            "data": {
                "type": "checkouts",
                "attributes": {
                    "checkout_data": {
                        "email": user_email,
                        "custom": {"user_id": user_id},
                    },
                    "product_options": {
                        "redirect_url": f"{APP_URL}/chat?payment=success"
                    },
                },
                "relationships": {
                    "store": {"data": {"type": "stores", "id": LEMONSQUEEZY_STORE_ID}},
                    "variant": {"data": {"type": "variants", "id": variant_id}},
                },
            }
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    f"{cls.API_BASE}/checkouts", headers=cls._headers(), json=payload
                )
                if resp.status_code == 201:
                    return resp.json()["data"]["attributes"]["url"]
            except Exception as e:
                logger.error(f"LemonSqueezy error: {e}")
        return None

    @staticmethod
    def verify_webhook(payload: bytes, signature: str) -> bool:
        if not LEMONSQUEEZY_WEBHOOK_SECRET:
            return False
        expected = hmac.new(
            LEMONSQUEEZY_WEBHOOK_SECRET.encode(), payload, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)


# ═══════════════════════════════════════════════════════════════
# 🌐 UNIFIED GATEWAY — Auto-pick provider
# ═══════════════════════════════════════════════════════════════

class PaymentGateway:
    """Unified payment gateway — auto-selects configured provider."""

    @staticmethod
    async def create_checkout(
        user_id: str,
        user_email: str,
        user_name: str = "",
        plan: str = "pro",
        provider: str = "auto",
        method: str = "card",
        is_token_package: bool = False,
        package_id: str = "",
    ) -> Dict[str, Any]:
        """
        Create checkout URL.
        provider: "auto" | "stripe" | "paymob" | "lemonsqueezy"
        method: "card" | "wallet" (Paymob only)
        """
        # Auto-detect
        if provider == "auto":
            if STRIPE_SECRET_KEY:
                provider = "stripe"
            elif PAYMOB_API_KEY:
                provider = "paymob"
            elif LEMONSQUEEZY_API_KEY:
                provider = "lemonsqueezy"
            else:
                return {"error": "لم يتم تكوين أي بوابة دفع", "checkout_url": None}

        url = None

        if provider == "stripe":
            url = await StripeProvider.create_checkout(
                user_id, user_email, plan, is_token_package, package_id
            )
        elif provider == "paymob":
            url = await PaymobProvider.create_checkout(
                user_id, user_email, user_name, plan, method,
                is_token_package, package_id,
            )
        elif provider == "lemonsqueezy":
            url = await LemonSqueezyProvider.create_checkout(user_id, user_email, plan)

        if url:
            return {"checkout_url": url, "provider": provider}
        return {"error": "فشل إنشاء رابط الدفع", "checkout_url": None}

    @staticmethod
    async def handle_webhook(
        provider: str, request_data: Dict, raw_body: bytes, headers: Dict, db_client
    ) -> Dict[str, Any]:
        """
        Process webhook from any provider.
        Returns {"success": bool, "user_id": str, "plan": str, "tokens": int}
        """

        if provider == "stripe":
            sig = headers.get("stripe-signature", "")
            event = StripeProvider.verify_webhook(raw_body, sig)
            if not event:
                return {"success": False, "error": "Invalid Stripe signature"}

            event_type = event.get("type", "")
            obj = event.get("data", {}).get("object", {})
            metadata = obj.get("metadata", {})
            user_id = metadata.get("user_id")

            if event_type == "checkout.session.completed":
                payment_type = metadata.get("type", "subscription")

                if payment_type == "tokens":
                    tokens = int(metadata.get("tokens", 0))
                    if user_id and tokens > 0:
                        await db_client.add_tokens(user_id, tokens)
                        logger.info(f"Stripe: Added {tokens} tokens to user {user_id}")
                        return {"success": True, "user_id": user_id, "tokens": tokens}

                elif payment_type == "subscription":
                    plan = metadata.get("plan", "pro")
                    plan_info = PLANS.get(plan, {})
                    tokens = plan_info.get("tokens", 0)
                    if user_id:
                        # Upgrade subscription
                        await db_client.execute(
                            "UPDATE users SET subscription_tier=?, subscription_expires=? WHERE id=? OR email=?",
                            (plan, (datetime.now() + timedelta(days=30)).isoformat(), user_id, user_id),
                        )
                        if tokens > 0:
                            await db_client.add_tokens(user_id, tokens)
                        logger.info(f"Stripe: {plan} subscription for user {user_id}")
                        return {"success": True, "user_id": user_id, "plan": plan, "tokens": tokens}

            return {"success": False, "error": f"Unhandled event: {event_type}"}

        elif provider == "paymob":
            hmac_received = request_data.get("hmac") or headers.get("hmac", "")
            if not PaymobProvider.verify_webhook(request_data, hmac_received):
                return {"success": False, "error": "Invalid Paymob HMAC"}

            obj = request_data.get("obj", request_data)
            success = obj.get("success", False)
            if not success:
                return {"success": False, "error": "Payment not successful"}

            # Extract merchant_order_id (can arrive in different shapes)
            merchant_order_id = ""
            order_val = obj.get("order")
            if isinstance(order_val, dict):
                merchant_order_id = str(order_val.get("merchant_order_id", ""))
            if not merchant_order_id:
                merchant_order_id = str(obj.get("merchant_order_id", "") or request_data.get("merchant_order_id", ""))

            # Parse user_id from merchant_order_id: robovai_{user_id}_{plan}_{timestamp}
            order_id_str = merchant_order_id
            parts = order_id_str.split("_")
            user_id = parts[1] if len(parts) >= 3 else None
            plan = parts[2] if len(parts) >= 3 else "pro"

            if user_id:
                plan_info = PLANS.get(plan, {})
                tokens = plan_info.get("tokens", 0)
                await db_client.execute(
                    "UPDATE users SET subscription_tier=?, subscription_expires=? WHERE id=? OR email=?",
                    (plan, (datetime.now() + timedelta(days=30)).isoformat(), user_id, user_id),
                )
                if tokens > 0:
                    await db_client.add_tokens(user_id, tokens)
                logger.info(f"Paymob: {plan} for user {user_id}, +{tokens} tokens")
                return {"success": True, "user_id": user_id, "plan": plan, "tokens": tokens}

            return {"success": False, "error": "Could not extract user_id"}

        elif provider == "lemonsqueezy":
            sig = headers.get("x-signature", "")
            if not LemonSqueezyProvider.verify_webhook(raw_body, sig):
                return {"success": False, "error": "Invalid LemonSqueezy signature"}

            event_name = request_data.get("meta", {}).get("event_name", "")
            custom = request_data.get("meta", {}).get("custom_data", {})
            user_id = custom.get("user_id")

            if event_name in ("subscription_created", "subscription_updated") and user_id:
                variant_id = str(request_data.get("data", {}).get("attributes", {}).get("variant_id", ""))
                plan = "pro" if variant_id == LEMON_PRO_VARIANT else "enterprise"
                ends_at = request_data.get("data", {}).get("attributes", {}).get("ends_at")
                plan_info = PLANS.get(plan, {})
                tokens = plan_info.get("tokens", 0)
                await db_client.execute(
                    "UPDATE users SET subscription_tier=?, subscription_expires=? WHERE id=? OR email=?",
                    (plan, ends_at, user_id, user_id),
                )
                if tokens > 0:
                    await db_client.add_tokens(user_id, tokens)
                return {"success": True, "user_id": user_id, "plan": plan}

            elif event_name == "subscription_cancelled" and user_id:
                await db_client.execute(
                    "UPDATE users SET subscription_tier='free' WHERE id=? OR email=?",
                    (user_id, user_id),
                )
                return {"success": True, "user_id": user_id, "plan": "free"}

        return {"success": False, "error": "Unknown provider"}

    @staticmethod
    def get_plans() -> Dict:
        return PLANS

    @staticmethod
    def get_token_packages() -> Dict:
        return TOKEN_PACKAGES

    @staticmethod
    def get_providers() -> List[str]:
        return get_active_providers()
