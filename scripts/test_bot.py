#!/usr/bin/env python3
"""
🔍 اختبار سريع للبوت
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

print("🧪 Testing Telegram Bot...\n")

# Get bot info
url = f"https://api.telegram.org/bot{TOKEN}/getMe"
response = requests.get(url)
data = response.json()

if data.get("ok"):
    bot = data['result']
    print(f"✅ Bot: @{bot['username']}")
    print(f"   Name: {bot['first_name']}")
    print(f"   ID: {bot['id']}")
else:
    print(f"❌ Error: {data.get('description')}")
    exit(1)

# Check recent updates
print("\n🔍 Checking recent activity...")
updates_url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?limit=5"
updates_response = requests.get(updates_url)
updates_data = updates_response.json()

if updates_data.get("ok"):
    updates = updates_data['result']
    if updates:
        print(f"\n📬 Last {len(updates)} updates:")
        for update in updates[-3:]:  # Show last 3
            if 'message' in update:
                msg = update['message']
                user = msg.get('from', {})
                text = msg.get('text', '[media]')
                print(f"   • {user.get('first_name')}: {text[:50]}")
    else:
        print("\n⚠️  No recent updates found.")
        print("   Send a message to the bot on Telegram and run this again.")

# Check webhook again
print("\n🔗 Webhook Status:")
webhook_url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
webhook_response = requests.get(webhook_url)
webhook_data = webhook_response.json()

if webhook_data.get("ok"):
    info = webhook_data['result']
    print(f"   URL: {info.get('url')}")
    print(f"   Pending: {info.get('pending_update_count', 0)}")
    
    if info.get('last_error_date'):
        from datetime import datetime
        error_time = datetime.fromtimestamp(info.get('last_error_date'))
        print(f"\n⚠️  Last Error: {error_time}")
        print(f"   Message: {info.get('last_error_message', 'Unknown')}")

print("\n" + "="*60)
print("✅ Bot is configured and waiting for messages!")
print("Send a message on Telegram to test: @robovainova_bot")
print("="*60)
