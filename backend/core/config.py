import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "RobovAI Universal"
    VERSION: str = "3.0.0"
    
    # Database
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # AI Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
    
    # Utility APIs
    AMDOREN_API_KEY: str = os.getenv("AMDOREN_API_KEY", "")
    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY", "")
    
    # Image APIs
    UNSPLASH_ACCESS_KEY: str = os.getenv("UNSPLASH_ACCESS_KEY", "")
    PEXELS_API_KEY: str = os.getenv("PEXELS_API_KEY", "")
    
    # Authentication & Routing
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    WORKOS_CLIENT_ID: str = os.getenv("WORKOS_CLIENT_ID", "")
    WORKOS_API_KEY: str = os.getenv("WORKOS_API_KEY", "")
    
    # Specialized APIs
    ART_SEARCH_API_KEY: str = os.getenv("ART_SEARCH_API_KEY", "")
    GOFILE_API_TOKEN: str = os.getenv("GOFILE_API_TOKEN", "")
    DDOWNLOAD_API_KEY: str = os.getenv("DDOWNLOAD_API_KEY", "")
    IMGBB_API_KEY: str = os.getenv("IMGBB_API_KEY", "")

    # ═══════════════════════════════════════════════════════════════
    # 📱 MULTI-PLATFORM INTEGRATION
    # ═══════════════════════════════════════════════════════════════
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # WhatsApp Business API
    WHATSAPP_ACCESS_TOKEN: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    WHATSAPP_PHONE_ID: str = os.getenv("WHATSAPP_PHONE_ID", "")
    WHATSAPP_VERIFY_TOKEN: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "robovai_verify")
    
    # Facebook Messenger
    MESSENGER_PAGE_TOKEN: str = os.getenv("MESSENGER_PAGE_TOKEN", "")
    MESSENGER_VERIFY_TOKEN: str = os.getenv("MESSENGER_VERIFY_TOKEN", "robovai_verify")
    
    # Discord
    DISCORD_BOT_TOKEN: str = os.getenv("DISCORD_BOT_TOKEN", "")
    DISCORD_APPLICATION_ID: str = os.getenv("DISCORD_APPLICATION_ID", "")

    # Models
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    # NVIDIA Specialized Models
    NVIDIA_GENERAL_MODEL: str = "meta/llama-3.1-405b-instruct"
    NVIDIA_CODING_MODEL: str = "meta/llama-4-maverick-17b-128e-instruct"
    NVIDIA_WRITING_MODEL: str = "nvidia/nemotron-3-nano-30b-a3b"
    NVIDIA_REASONING_MODEL: str = "deepseek-ai/deepseek-coder-6.7b-instruct" 
    NVIDIA_VISION_MODEL: str = "nvidia/cosmos-nemotron-34b"
    NVIDIA_OCR_MODEL: str = "nvidia/nemoretriever-ocr-v1"
    NVIDIA_SAFETY_MODEL: str = "nvidia/nemotron-content-safety-reasoning-4b"
    NVIDIA_MODEL: str = "meta/llama-3.1-405b-instruct"

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra env vars not defined here

settings = Settings()

