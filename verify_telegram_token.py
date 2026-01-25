import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not found in .env")
    exit(1)

url = f"https://api.telegram.org/bot{TOKEN}/getMe"

try:
    response = requests.get(url)
    data = response.json()
    
    if data.get("ok"):
        print(f"✅ Telegram Bot Token is VALID.")
        print(f"Bot Name: {data['result']['first_name']}")
        print(f"Bot Username: @{data['result']['username']}")
        print(f"Bot ID: {data['result']['id']}")
    else:
        print(f"❌ Telegram Bot Token is INVALID.")
        print(f"Error: {data.get('description')}")
        
except Exception as e:
    print(f"❌ Error connecting to Telegram API: {e}")
