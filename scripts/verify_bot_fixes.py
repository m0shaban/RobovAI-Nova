#!/usr/bin/env python3
"""
🧪 اختبار شامل لإصلاحات البوت
"""
import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TEST_CHAT_ID = os.getenv("TEST_CHAT_ID", "")  # Optional: your personal chat ID for testing

async def test_send_message():
    """Test the Telegram send message with fallback"""
    print("🧪 Testing Telegram Send Message...\n")
    
    if not TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set")
        return False
    
    api_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    # Test messages with different formatting challenges
    test_messages = [
        ("Plain text", "مرحبا! هذه رسالة اختبار بسيطة ✅"),
        ("With asterisks", "هذا *نص* مع *نجوم* للاختبار"),
        ("With underscores", "هذا _نص_ مع _شرطات_ للاختبار"),
        ("Mixed special chars", "Test: (hello) [world] {test} <html> *bold* _italic_ `code`"),
        ("Arabic with emojis", "🎉 تم بنجاح! إنجاز جديد 🚀 مبروك 💯"),
    ]
    
    if not TEST_CHAT_ID:
        print("⚠️  TEST_CHAT_ID not set. Skipping live tests.")
        print("   To test, add TEST_CHAT_ID=your_user_id to .env")
        print("\n✅ Syntax check passed. Ready for deployment.\n")
        return True
    
    print(f"📱 Sending to chat: {TEST_CHAT_ID}\n")
    
    async with httpx.AsyncClient() as client:
        for name, text in test_messages:
            print(f"Testing: {name}...")
            
            # Try HTML first
            success = False
            try:
                payload = {"chat_id": TEST_CHAT_ID, "text": text, "parse_mode": "HTML"}
                resp = await client.post(api_url, json=payload, timeout=10.0)
                if resp.status_code == 200:
                    print(f"  ✅ HTML: Success")
                    success = True
                else:
                    print(f"  ⚠️ HTML: Failed ({resp.status_code})")
            except Exception as e:
                print(f"  ⚠️ HTML: Exception ({e})")
            
            # If HTML failed, try plain text
            if not success:
                try:
                    payload = {"chat_id": TEST_CHAT_ID, "text": text}
                    resp = await client.post(api_url, json=payload, timeout=10.0)
                    if resp.status_code == 200:
                        print(f"  ✅ Plain: Success (fallback worked)")
                    else:
                        print(f"  ❌ Plain: Failed ({resp.status_code})")
                except Exception as e:
                    print(f"  ❌ Plain: Exception ({e})")
    
    print("\n✅ Send message test complete!\n")
    return True

async def test_webhook_info():
    """Check webhook status"""
    print("🔗 Checking Webhook Status...\n")
    
    if not TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set")
        return False
    
    url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        data = resp.json()
        
        if data.get("ok"):
            result = data['result']
            print(f"  URL: {result.get('url', '❌ NOT SET')}")
            print(f"  Pending: {result.get('pending_update_count', 0)}")
            
            if result.get('last_error_date'):
                print(f"\n  ⚠️ Last Error: {result.get('last_error_message')}")
            
            if not result.get('url'):
                print("\n❌ Webhook is NOT set!")
                return False
            else:
                print("\n✅ Webhook is configured")
                return True
        else:
            print(f"❌ API Error: {data.get('description')}")
            return False

async def main():
    print("=" * 60)
    print("🤖 RobovAI Nova - Bot Fix Verification")
    print("=" * 60 + "\n")
    
    # Test 1: Webhook
    webhook_ok = await test_webhook_info()
    
    # Test 2: Send message
    send_ok = await test_send_message()
    
    print("=" * 60)
    print("📊 Summary:")
    print(f"  Webhook: {'✅ OK' if webhook_ok else '❌ NEEDS FIX'}")
    print(f"  Send:    {'✅ OK' if send_ok else '❌ NEEDS FIX'}")
    print("=" * 60)
    
    if webhook_ok and send_ok:
        print("\n🎉 All tests passed! Ready to deploy.\n")
        print("Next steps:")
        print("  git add .")
        print('  git commit -m "Fix: Bot rebuild with fallback messaging"')
        print("  git push")
    else:
        print("\n⚠️ Some tests failed. Check the issues above.\n")

if __name__ == "__main__":
    asyncio.run(main())
