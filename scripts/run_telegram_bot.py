
import asyncio
import logging
from dotenv import load_dotenv
import os
import sys

# Add parent directory to path to import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load env before imports
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

from backend.telegram_bot import create_telegram_app

def main():
    """Run the bot in polling mode"""
    logger.info("🚀 Starting Telegram Bot in POLLING mode...")
    
    application = create_telegram_app()
    
    if not application:
        logger.error("❌ Failed to create bot application. Check your token.")
        return

    # Run the bot
    logger.info("✅ Bot is running! Press Ctrl+C to stop.")
    application.run_polling()

if __name__ == "__main__":
    main()
