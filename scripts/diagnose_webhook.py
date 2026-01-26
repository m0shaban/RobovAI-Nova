#!/usr/bin/env python3
"""
تحقق سريع من حالة الـ Webhook
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("EXTERNAL_URL")

if not TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not found")
    exit(1)

print("🔍 Checking Telegram Webhook Status...\n")

# 1. Get current webhook info
url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
response = requests.get(url)
data = response.json()

if data.get("ok"):
    result = data['result']
    print("📊 Current Webhook Configuration:")
    print(f"  URL: {result.get('url', '❌ NOT SET')}")
    print(f"  Pending Updates: {result.get('pending_update_count', 0)}")
    
    if result.get('last_error_date'):
        from datetime import datetime
        error_time = datetime.fromtimestamp(result.get('last_error_date'))
        print(f"\n⚠️  Last Error:")
        print(f"  Time: {error_time}")
        print(f"  Message: {result.get('last_error_message', 'Unknown')}")
    
    current_webhook = result.get('url', '')
    
    # 2. Check if webhook needs to be set
    if not current_webhook:
        print("\n❌ PROBLEM: Webhook is NOT set!")
        if RENDER_URL:
            print(f"\n💡 Solution: Set webhook to: {RENDER_URL}/telegram-webhook")
            print("\nRun this command:")
            print(f'curl "https://api.telegram.org/bot{TOKEN}/setWebhook?url={RENDER_URL}/telegram-webhook"')
        else:
            print("\n⚠️  RENDER_EXTERNAL_URL not found in .env")
            print("You need to set it in Render Dashboard > Environment")
    else:
        expected = f"{RENDER_URL}/telegram-webhook" if RENDER_URL else None
        if expected and current_webhook != expected:
            print(f"\n⚠️  WARNING: Webhook URL mismatch!")
            print(f"  Current:  {current_webhook}")
            print(f"  Expected: {expected}")
        else:
            print("\n✅ Webhook URL looks correct")
            
            # 3. Test if webhook URL is reachable
            print(f"\n🔍 Testing if {current_webhook} is reachable...")
            try:
                test_response = requests.get(current_webhook.replace('/telegram-webhook', '/health'), timeout=5)
                if test_response.status_code == 200:
                    print("✅ Render app is responding!")
                else:
                    print(f"⚠️  Got status code: {test_response.status_code}")
            except Exception as e:
                print(f"❌ Cannot reach Render app: {e}")

else:
    print(f"❌ API Error: {data.get('description')}")

print("\n" + "="*60)
print("Next Steps:")
print("1. Check Render logs for errors")
print("2. Verify EXTERNAL_URL is set in Render environment")
print("3. If webhook not set, run the curl command above")
print("="*60)
