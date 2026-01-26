#!/usr/bin/env python3
"""
🔍 Telegram Bot Health Check
Verifies bot configuration and logs setup
"""

import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_env():
    """Check environment variables"""
    logger.info("🔍 Checking environment variables...")
    
    required_vars = [
        "TELEGRAM_BOT_TOKEN",
        "GROQ_API_KEY",
    ]
    
    optional_vars = [
        "EXTERNAL_URL",
        "RENDER_EXTERNAL_URL",
    ]
    
    all_ok = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✅ {var}: {'*' * 20}")
        else:
            logger.error(f"❌ {var}: NOT SET")
            all_ok = False
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"ℹ️  {var}: {value}")
        else:
            logger.warning(f"⚠️  {var}: not set (optional)")
    
    return all_ok

def check_imports():
    """Check that all required libraries are available"""
    logger.info("🔍 Checking imports...")
    
    imports_to_check = [
        ("telegram", "python-telegram-bot"),
        ("fastapi", "fastapi"),
        ("dotenv", "python-dotenv"),
    ]
    
    all_ok = True
    
    for module_name, package_name in imports_to_check:
        try:
            __import__(module_name)
            logger.info(f"✅ {package_name} installed")
        except ImportError:
            logger.error(f"❌ {package_name} NOT installed")
            all_ok = False
    
    return all_ok

def test_telegram_bot():
    """Test Telegram bot initialization"""
    logger.info("🔍 Testing Telegram bot initialization...")
    
    try:
        from backend.telegram_bot import create_telegram_app
        
        app = create_telegram_app()
        
        if app:
            logger.info("✅ Telegram bot app created successfully")
            return True
        else:
            logger.error("❌ Telegram bot app creation returned None")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to create Telegram bot app: {e}", exc_info=True)
        return False

def main():
    """Run all checks"""
    print("=" * 60)
    print("🤖 RobovAI Telegram Bot Health Check")
    print("=" * 60)
    print()
    
    checks = [
        ("Environment Variables", check_env),
        ("Python Imports", check_imports),
        ("Telegram Bot Initialization", test_telegram_bot),
    ]
    
    results = []
    
    for name, check_func in checks:
        print(f"\n{'=' * 60}")
        print(f"Testing: {name}")
        print('=' * 60)
        result = check_func()
        results.append((name, result))
        print()
    
    print("=" * 60)
    print("📊 Summary")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if not result:
            all_passed = False
    
    print()
    
    if all_passed:
        print("🎉 All checks passed! Bot is ready to deploy.")
        return 0
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
