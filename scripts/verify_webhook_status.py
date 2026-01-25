import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not found in .env")
    exit(1)

url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"

try:
    response = requests.get(url)
    data = response.json()
    
    if data.get("ok"):
        result = data['result']
        print("\n🔍 Telegram Webhook Status:")
        print(f"URL: {result.get('url', 'Not Set')}")
        print(f"Has Custom Certificate: {result.get('has_custom_certificate')}")
        print(f"Pending Update Count: {result.get('pending_update_count')}")
        if result.get('last_error_date'):
            print(f"Last Error Date: {result.get('last_error_date')}")
            print(f"Last Error Message: {result.get('last_error_message')}")
            
        if not result.get('url'):
            print("\n⚠️ Webhook is NOT set. The bot will not receive messages on Render.")
            print("To fix this, ensure EXTERNAL_URL is set in Render Environment Variables.")
        else:
            print("\n✅ Webhook is currently set.")
    else:
        print(f"❌ Error getting webhook info: {data.get('description')}")
        
except Exception as e:
    print(f"❌ Error connecting to Telegram API: {e}")
