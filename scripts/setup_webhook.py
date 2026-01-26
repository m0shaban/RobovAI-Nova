#!/usr/bin/env python3
"""
🔧 ضبط الـ Webhook للـ Telegram Bot
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not found")
    exit(1)

print("🚀 Setting up Telegram Webhook\n")
print("=" * 60)

# Get Render URL from user
print("\n📋 Step 1: Get your Render URL")
print("   Go to: https://dashboard.render.com/web/srv-d5r2m9i4d50c738pbqf0")
print("   Copy the URL (should be like: https://your-app.onrender.com)\n")

render_url = input("📝 Paste your Render URL here: ").strip()

if not render_url:
    print("❌ No URL provided!")
    exit(1)

# Remove trailing slash
render_url = render_url.rstrip('/')

# Construct webhook URL
webhook_url = f"{render_url}/telegram-webhook"

print(f"\n🔗 Setting webhook to: {webhook_url}")

# Set webhook
set_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
data = {"url": webhook_url}

try:
    response = requests.post(set_url, json=data)
    result = response.json()
    
    if result.get("ok"):
        print("\n✅ SUCCESS! Webhook has been set!")
        print(f"   URL: {webhook_url}")
        
        # Verify it was set
        print("\n🔍 Verifying...")
        verify_url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
        verify_response = requests.get(verify_url)
        verify_data = verify_response.json()
        
        if verify_data.get("ok"):
            info = verify_data['result']
            print(f"   Current Webhook: {info.get('url')}")
            print(f"   Pending Updates: {info.get('pending_update_count', 0)}")
            
            if info.get('pending_update_count', 0) > 0:
                print("\n🎉 The bot will now process the pending messages!")
            
        print("\n" + "=" * 60)
        print("✅ DONE! Your bot should now work!")
        print("Try sending a message on Telegram now.")
        print("=" * 60)
    else:
        print(f"\n❌ Failed to set webhook: {result.get('description')}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
