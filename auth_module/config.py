"""
⚙️ Auth Module — Configuration
"""

import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class AuthSettings(BaseSettings):
    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Database
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "users.db")

    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # App
    EXTERNAL_URL: str = os.getenv(
        "EXTERNAL_URL", os.getenv("RENDER_EXTERNAL_URL", "https://robovai.com")
    )

    class Config:
        env_file = ".env"
        extra = "ignore"


auth_settings = AuthSettings()
