#!/usr/bin/env python3
"""
🎯 ضبط قائمة الأوامر في Telegram Bot
Sets the bot menu commands that appear when user clicks "Menu" button
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not found in .env")
    exit(1)

print("🎯 Setting Telegram Bot Menu Commands\n")
print("=" * 70)

# Define bot commands
commands = [
    {"command": "start", "description": "🚀 بدء استخدام البوت"},
    {"command": "help", "description": "ℹ️ قائمة المساعدة"},
    {"command": "tools", "description": "🛠️ قائمة الأدوات المتاحة"},
    {"command": "menu", "description": "📋 القائمة الرئيسية"},
    
    # Creative tools
    {"command": "generate_image", "description": "🎨 توليد صورة بالذكاء الاصطناعي"},
    {"command": "qr", "description": "📱 إنشاء QR Code"},
    {"command": "chart", "description": "📊 إنشاء مخطط بياني"},
    {"command": "diagram", "description": "📐 رسم مخطط"},
    
    # Web & Data
    {"command": "search", "description": "🔍 بحث في الويب"},
    {"command": "weather", "description": "🌤️ حالة الطقس"},
    {"command": "translate", "description": "🌐 ترجمة نص"},
    {"command": "wikipedia", "description": "📚 بحث في ويكيبيديا"},
    
    # Fun
    {"command": "joke", "description": "😂 نكتة"},
    {"command": "quote", "description": "💭 اقتباس"},
    {"command": "cat", "description": "🐱 صورة قطة عشوائية"},
    {"command": "dog", "description": "🐕 صورة كلب عشوائي"},
]

# Set commands
url = f"https://api.telegram.org/bot{TOKEN}/setMyCommands"

try:
    response = requests.post(url, json={"commands": commands})
    result = response.json()
    
    if result.get("ok"):
        print("✅ SUCCESS! Bot menu commands have been set!\n")
        print("Commands list:")
        print("-" * 70)
        for cmd in commands:
            print(f"  /{cmd['command']:<20} - {cmd['description']}")
        
        print("\n" + "=" * 70)
        print("✅ DONE! The new menu is now live!")
        print("Open your Telegram bot and click 'Menu' to see the changes.")
        print("=" * 70)
    else:
        print(f"❌ Failed: {result.get('description')}")
        
except Exception as e:
    print(f"❌ Error: {e}")
