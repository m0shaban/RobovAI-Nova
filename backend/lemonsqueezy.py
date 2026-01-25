"""
💳 RobovAI Nova - LemonSqueezy Payment Integration
═══════════════════════════════════════════════════════════════

Simple payment integration with:
- Checkout links
- Webhook handling
- Subscription management
"""

import os
import hmac
import hashlib
import httpx
from datetime import datetime
from typing import Optional, Dict
import logging

logger = logging.getLogger("robovai.payments")

# LemonSqueezy Configuration
LEMONSQUEEZY_API_KEY = os.getenv("LEMONSQUEEZY_API_KEY", "")
LEMONSQUEEZY_STORE_ID = os.getenv("LEMONSQUEEZY_STORE_ID", "")
LEMONSQUEEZY_WEBHOOK_SECRET = os.getenv("LEMONSQUEEZY_WEBHOOK_SECRET", "")

# Product IDs (set these after creating products in LemonSqueezy dashboard)
PRODUCTS = {
    "pro": os.getenv("LEMONSQUEEZY_PRO_VARIANT_ID", ""),
    "enterprise": os.getenv("LEMONSQUEEZY_ENTERPRISE_VARIANT_ID", "")
}

class LemonSqueezyPayment:
    """LemonSqueezy payment handler"""
    
    API_BASE = "https://api.lemonsqueezy.com/v1"
    
    @staticmethod
    def get_headers():
        return {
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
            "Authorization": f"Bearer {LEMONSQUEEZY_API_KEY}"
        }
    
    @staticmethod
    async def create_checkout(user_id: str, user_email: str, tier: str = "pro") -> Optional[str]:
        """Create checkout URL for user"""
        variant_id = PRODUCTS.get(tier)
        
        if not variant_id or not LEMONSQUEEZY_API_KEY:
            logger.warning("LemonSqueezy not configured")
            return None
        
        payload = {
            "data": {
                "type": "checkouts",
                "attributes": {
                    "checkout_data": {
                        "email": user_email,
                        "custom": {
                            "user_id": user_id
                        }
                    },
                    "product_options": {
                        "redirect_url": "https://robovai-nova.onrender.com/chat?payment=success"
                    }
                },
                "relationships": {
                    "store": {
                        "data": {
                            "type": "stores",
                            "id": LEMONSQUEEZY_STORE_ID
                        }
                    },
                    "variant": {
                        "data": {
                            "type": "variants",
                            "id": variant_id
                        }
                    }
                }
            }
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{LemonSqueezyPayment.API_BASE}/checkouts",
                    headers=LemonSqueezyPayment.get_headers(),
                    json=payload
                )
                
                if response.status_code == 201:
                    data = response.json()
                    checkout_url = data["data"]["attributes"]["url"]
                    logger.info(f"Created checkout for user {user_id}: {checkout_url}")
                    return checkout_url
                else:
                    logger.error(f"Checkout creation failed: {response.text}")
                    return None
                    
            except Exception as e:
                logger.error(f"LemonSqueezy error: {e}")
                return None
    
    @staticmethod
    def verify_webhook(payload: bytes, signature: str) -> bool:
        """Verify webhook signature"""
        if not LEMONSQUEEZY_WEBHOOK_SECRET:
            return False
        
        expected = hmac.new(
            LEMONSQUEEZY_WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature)
    
    @staticmethod
    async def process_webhook(event_name: str, data: Dict, db_client) -> bool:
        """Process webhook event"""
        
        if event_name == "subscription_created":
            # New subscription
            custom_data = data.get("meta", {}).get("custom_data", {})
            user_id = custom_data.get("user_id")
            
            if user_id:
                variant_id = str(data.get("data", {}).get("attributes", {}).get("variant_id", ""))
                tier = "pro" if variant_id == PRODUCTS.get("pro") else "enterprise"
                
                # Get subscription end date
                ends_at = data.get("data", {}).get("attributes", {}).get("ends_at")
                
                await db_client.execute("""
                    INSERT OR REPLACE INTO subscriptions 
                    (user_id, tier, expires_at, created_at)
                    VALUES (?, ?, ?, ?)
                """, (user_id, tier, ends_at, datetime.now().isoformat()))
                
                logger.info(f"Activated {tier} subscription for user {user_id}")
                return True
        
        elif event_name == "subscription_updated":
            # Subscription renewed or changed
            custom_data = data.get("meta", {}).get("custom_data", {})
            user_id = custom_data.get("user_id")
            
            if user_id:
                ends_at = data.get("data", {}).get("attributes", {}).get("ends_at")
                status = data.get("data", {}).get("attributes", {}).get("status")
                
                if status == "active":
                    await db_client.execute("""
                        UPDATE subscriptions SET expires_at = ? WHERE user_id = ?
                    """, (ends_at, user_id))
                    logger.info(f"Updated subscription for user {user_id}")
                
                return True
        
        elif event_name == "subscription_cancelled":
            # Subscription cancelled
            custom_data = data.get("meta", {}).get("custom_data", {})
            user_id = custom_data.get("user_id")
            
            if user_id:
                await db_client.execute("""
                    UPDATE subscriptions SET tier = 'free' WHERE user_id = ?
                """, (user_id,))
                logger.info(f"Cancelled subscription for user {user_id}")
                return True
        
        return False
    
    @staticmethod
    async def get_customer_portal_url(user_id: str, db_client) -> Optional[str]:
        """Get customer portal URL for managing subscription"""
        # This would require storing the customer_id from LemonSqueezy
        # For now, return the main LemonSqueezy billing URL
        return "https://app.lemonsqueezy.com/my-orders"


# Pricing display helper
PRICING_TIERS = {
    "free": {
        "name": "مجاني",
        "name_en": "Free",
        "price": 0,
        "requests_per_day": 100,
        "features": [
            "112 أداة ذكية",
            "100 طلب/يوم",
            "دعم المجتمع"
        ]
    },
    "pro": {
        "name": "احترافي",
        "name_en": "Pro",
        "price": 5,
        "requests_per_day": 1000,
        "features": [
            "كل الأدوات",
            "1,000 طلب/يوم",
            "دعم أولوية",
            "بدون إعلانات",
            "API Access"
        ]
    },
    "enterprise": {
        "name": "مؤسسات",
        "name_en": "Enterprise",
        "price": 50,
        "requests_per_day": -1,  # Unlimited
        "features": [
            "طلبات غير محدودة",
            "تكاملات مخصصة",
            "دعم مخصص 24/7",
            "SLA مضمون",
            "Whitelabel"
        ]
    }
}
