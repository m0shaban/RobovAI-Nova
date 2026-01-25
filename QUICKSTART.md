# 🚀 RobovAI Nova - Quick Start Guide

## ✅ Phase 2 Complete

### What's New

1. **🎨 Landing Page** - Professional design at `/`
2. **🤖 Telegram Bot** - Full integration with menu/shortcuts
3. **💳 Payment System** - 3 tiers (Free, Pro, Enterprise)
4. **🔐 OTP Verification** - Via Telegram
5. **📈 Usage Tracking** - Analytics & limits

---

## 🔧 Setup Telegram Bot

### 1. Get Bot Token

```bash
# Talk to @BotFather on Telegram
/newbot
# Follow instructions to get token
```

### 2. Add to Render

1. Go to Render Dashboard
2. Select `robovai-nova` service
3. Environment → Add Variable:
   - **Key**: `TELEGRAM_BOT_TOKEN`
   - **Value**: Your bot token
4. Save (auto-redeploys)

### 3. Set Webhook

```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=https://robovai-nova.onrender.com/telegram-webhook"
```

### 4. Test

- Open your bot on Telegram
- Send `/start`
- You should see the welcome message with buttons!

---

## 💳 Payment Tiers

| Tier | Price | Requests/Day | Features |
|------|-------|--------------|----------|
| **Free** | $0 | 100 | Basic tools |
| **Pro** | $5/mo | 1,000 | All tools, Priority support |
| **Enterprise** | $50/mo | Unlimited | Custom integrations, API |

---

## 📱 How Users Subscribe

### Via Telegram Bot

```
User: /start
Bot: [Shows menu with "Upgrade to Pro" button]
User: [Clicks button]
Bot: [Sends Telegram Payment invoice]
User: [Pays via Telegram]
Bot: ✅ Subscription activated!
```

### Via Web

- Coming soon: Stripe integration

---

## 🔐 OTP Verification Example

```python
# User signs up
otp = await OTPSystem.create_otp(user_id, "email_verification", db)
await OTPSystem.send_otp_telegram(user_id, otp, telegram_bot)

# User receives: "Your code: 123456"
# User enters code
is_valid = await OTPSystem.verify_otp(user_id, "123456", "email_verification", db)
```

---

## 📊 Check User Stats

```python
from backend.payments import UsageTracker

stats = await UsageTracker.get_user_stats(user_id, db)
# Returns:
# {
#   "total_requests": 1250,
#   "today_requests": 45,
#   "top_tools": ["/generate_image", "/weather", ...],
#   "subscription": {"tier": "pro", "expires_at": "2026-02-25"}
# }
```

---

## 🌐 Live URLs

- **Landing**: <https://robovai-nova.onrender.com>
- **Chat**: <https://robovai-nova.onrender.com/chat>
- **Developers**: <https://robovai-nova.onrender.com/developers>
- **Health**: <https://robovai-nova.onrender.com/health>

---

## ⚡ Quick Commands

```bash
# Local development
python -m uvicorn backend.main:app --reload

# Check database
sqlite3 users.db "SELECT * FROM subscriptions;"

# View logs
# (On Render dashboard)
```

---

## 🎯 What's Next?

- [ ] Test Telegram bot with real users
- [ ] Monitor payment conversions
- [ ] Build admin dashboard
- [ ] Add more payment methods (Stripe, PayPal)

🎉 **System is live and ready!**
