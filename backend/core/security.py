"""
🔐 Security Module
Handles password hashing and JWT token generation.
"""

from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
import jwt  # Needs: pip install pyjwt
from passlib.context import CryptContext  # Needs: pip install passlib[bcrypt]
import os
from .config import settings

# Configuration
SECRET_KEY = (
    settings.SUPABASE_KEY
    if len(settings.SUPABASE_KEY) > 20
    else "super_secret_fallback_key_change_in_prod"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

# Password Hashing
# Use PBKDF2-SHA256 to avoid bcrypt native dependency issues on some systems
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if password matches hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify a JWT token"""
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_token
    except jwt.PyJWTError:
        return None
