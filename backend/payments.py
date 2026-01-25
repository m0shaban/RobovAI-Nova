"""
💳 RobovAI Nova - Payment & Subscription System
═══════════════════════════════════════════════════════════════

Features:
- Telegram Payments integration
- Subscription tiers (Free, Pro, Enterprise)
- Usage tracking and limits
- Payment webhooks
"""

from datetime import datetime, timedelta
from typing import Optional, Dict
import secrets

class SubscriptionTier:
    """Subscription tier definitions"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    
    LIMITS = {
        FREE: {
            "requests_per_day": 100,
            "requests_per_month": 3000,
            "price": 0,
            "features": ["Basic tools", "100 requests/day"]
        },
        PRO: {
            "requests_per_day": 1000,
            "requests_per_month": 30000,
            "price": 5,  # USD per month
            "features": ["All tools", "1000 requests/day", "Priority support", "No ads"]
        },
        ENTERPRISE: {
            "requests_per_day": -1,  # Unlimited
            "requests_per_month": -1,
            "price": 50,  # USD per month
            "features": ["Unlimited requests", "Custom integrations", "Dedicated support", "API access"]
        }
    }

class PaymentSystem:
    """Handle payments and subscriptions"""
    
    @staticmethod
    async def create_invoice(user_id: str, tier: str, db_client):
        """Create Telegram payment invoice"""
        from telegram import LabeledPrice
        
        tier_info = SubscriptionTier.LIMITS.get(tier)
        if not tier_info or tier == SubscriptionTier.FREE:
            return None
        
        # Create invoice
        title = f"RobovAI Nova - {tier.upper()} Plan"
        description = f"Subscription: {', '.join(tier_info['features'])}"
        payload = f"subscription_{tier}_{user_id}_{secrets.token_hex(8)}"
        currency = "USD"
        prices = [LabeledPrice(label=f"{tier.upper()} Plan", amount=tier_info['price'] * 100)]
        
        return {
            "title": title,
            "description": description,
            "payload": payload,
            "currency": currency,
            "prices": prices
        }
    
    @staticmethod
    async def process_payment(payment_data: Dict, db_client):
        """Process successful payment"""
        # Extract payment info
        payload = payment_data.get("invoice_payload", "")
        
        # Parse payload: subscription_{tier}_{user_id}_{token}
        parts = payload.split("_")
        if len(parts) < 3:
            return False
        
        tier = parts[1]
        user_id = parts[2]
        
        # Update user subscription
        expires_at = (datetime.now() + timedelta(days=30)).isoformat()
        
        await db_client.execute("""
            INSERT OR REPLACE INTO subscriptions 
            (user_id, tier, expires_at, created_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, tier, expires_at, datetime.now().isoformat()))
        
        return True
    
    @staticmethod
    async def check_subscription(user_id: str, db_client) -> Dict:
        """Check user's subscription status"""
        result = await db_client.execute("""
            SELECT tier, expires_at FROM subscriptions
            WHERE user_id = ? AND expires_at > ?
        """, (user_id, datetime.now().isoformat()))
        
        if result:
            return {
                "tier": result[0]["tier"],
                "expires_at": result[0]["expires_at"],
                "active": True
            }
        
        return {
            "tier": SubscriptionTier.FREE,
            "expires_at": None,
            "active": False
        }
    
    @staticmethod
    async def check_usage_limit(user_id: str, db_client) -> bool:
        """Check if user has exceeded usage limits"""
        # Get subscription
        subscription = await PaymentSystem.check_subscription(user_id, db_client)
        tier = subscription["tier"]
        limits = SubscriptionTier.LIMITS[tier]
        
        # Unlimited for enterprise
        if limits["requests_per_day"] == -1:
            return True
        
        # Count today's requests
        today = datetime.now().date().isoformat()
        result = await db_client.execute("""
            SELECT COUNT(*) as count FROM usage_logs
            WHERE user_id = ? AND DATE(timestamp) = ?
        """, (user_id, today))
        
        count = result[0]["count"] if result else 0
        
        return count < limits["requests_per_day"]


class OTPSystem:
    """OTP verification system"""
    
    @staticmethod
    def generate_otp() -> str:
        """Generate 6-digit OTP"""
        return str(secrets.randbelow(900000) + 100000)
    
    @staticmethod
    async def create_otp(user_id: str, purpose: str, db_client) -> str:
        """Create and store OTP"""
        otp = OTPSystem.generate_otp()
        expires_at = (datetime.now() + timedelta(minutes=5)).isoformat()
        
        await db_client.execute("""
            INSERT INTO otp_codes (user_id, code, purpose, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, otp, purpose, expires_at, datetime.now().isoformat()))
        
        return otp
    
    @staticmethod
    async def verify_otp(user_id: str, code: str, purpose: str, db_client) -> bool:
        """Verify OTP code"""
        result = await db_client.execute("""
            SELECT * FROM otp_codes
            WHERE user_id = ? AND code = ? AND purpose = ? 
            AND expires_at > ? AND used = 0
            ORDER BY created_at DESC LIMIT 1
        """, (user_id, code, purpose, datetime.now().isoformat()))
        
        if not result:
            return False
        
        # Mark as used
        await db_client.execute("""
            UPDATE otp_codes SET used = 1 WHERE id = ?
        """, (result[0]["id"],))
        
        return True
    
    @staticmethod
    async def send_otp_telegram(user_id: str, otp: str, telegram_bot):
        """Send OTP via Telegram"""
        message = f"""
🔐 **كود التحقق الخاص بك**

الكود: `{otp}`

⏰ صالح لمدة 5 دقائق
⚠️ لا تشارك هذا الكود مع أحد!
        """
        await telegram_bot.send_message(chat_id=user_id, text=message, parse_mode='Markdown')


class UsageTracker:
    """Track user usage and analytics"""
    
    @staticmethod
    async def log_request(user_id: str, tool_name: str, platform: str, db_client):
        """Log a tool usage request"""
        await db_client.execute("""
            INSERT INTO usage_logs (user_id, tool_name, platform, timestamp)
            VALUES (?, ?, ?, ?)
        """, (user_id, tool_name, platform, datetime.now().isoformat()))
    
    @staticmethod
    async def get_user_stats(user_id: str, db_client) -> Dict:
        """Get user usage statistics"""
        # Total requests
        total = await db_client.execute("""
            SELECT COUNT(*) as count FROM usage_logs WHERE user_id = ?
        """, (user_id,))
        
        # Today's requests
        today = datetime.now().date().isoformat()
        today_count = await db_client.execute("""
            SELECT COUNT(*) as count FROM usage_logs
            WHERE user_id = ? AND DATE(timestamp) = ?
        """, (user_id, today))
        
        # Most used tools
        top_tools = await db_client.execute("""
            SELECT tool_name, COUNT(*) as count FROM usage_logs
            WHERE user_id = ?
            GROUP BY tool_name
            ORDER BY count DESC
            LIMIT 5
        """, (user_id,))
        
        # Subscription info
        subscription = await PaymentSystem.check_subscription(user_id, db_client)
        
        return {
            "total_requests": total[0]["count"] if total else 0,
            "today_requests": today_count[0]["count"] if today_count else 0,
            "top_tools": top_tools or [],
            "subscription": subscription
        }
