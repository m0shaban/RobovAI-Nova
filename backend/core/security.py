"""
🔐 Security Module — RobovAI Nova
═══════════════════════════════════════════
• Independent JWT secret (not Supabase key)
• Role-based access (user / admin)
• 24-hour token expiry (actually enforced)
• Password strength validation
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt  # Needs: pip install pyjwt
from passlib.context import CryptContext
import os, secrets, re

# ─── Independent JWT Secret ───────────────────────────────────
# Priority: env var → auto-generated (persisted in .jwt_secret)
_SECRET_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".jwt_secret"
)


def _load_or_create_secret() -> str:
    """Load JWT secret — prefers env var, warns loudly if falling back to file.
    In production (RENDER / ENVIRONMENT=production) the env var is REQUIRED."""
    env = os.getenv("JWT_SECRET_KEY", "").strip()
    if env and len(env) >= 32:
        return env

    # Production guard: env var MUST be set
    is_production = os.getenv("RENDER") or os.getenv("ENVIRONMENT", "").lower() == "production"
    if is_production:
        import sys
        print(
            "❌ CRITICAL: JWT_SECRET_KEY env var is missing or too short (min 32 chars). "
            "Set it in your hosting dashboard to prevent session invalidation on redeploy.",
            file=sys.stderr,
        )
        # Still generate one so the app can start, but sessions WILL break on restart
        return secrets.token_urlsafe(64)

    # Development fallback: persist to file
    if os.path.exists(_SECRET_FILE):
        with open(_SECRET_FILE, "r") as f:
            stored = f.read().strip()
            if len(stored) >= 32:
                return stored
    new_secret = secrets.token_urlsafe(64)
    try:
        with open(_SECRET_FILE, "w") as f:
            f.write(new_secret)
    except Exception:
        pass
    return new_secret


SECRET_KEY = _load_or_create_secret()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

# ─── Password Hashing ─────────────────────────────────────────
# Support legacy hashes (bcrypt) + current default (pbkdf2_sha256).
# This prevents older accounts from breaking after hashing changes.
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def verify_password_and_update(
    plain_password: str, hashed_password: str
) -> tuple[bool, str | None]:
    """Verify password and optionally return an upgraded hash.

    Returns:
        (ok, new_hash)
        - ok: True if verification succeeded
        - new_hash: new hash string if the existing one should be upgraded
    """
    try:
        ok, new_hash = pwd_context.verify_and_update(plain_password, hashed_password)
        return bool(ok), new_hash
    except Exception:
        # If the stored hash is malformed or from an unknown scheme, fail closed.
        return False, None


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Check password meets minimum requirements."""
    if len(password) < 6:
        return False, "كلمة المرور يجب أن تكون 6 أحرف على الأقل"
    if not re.search(r"[A-Za-z]", password):
        return False, "كلمة المرور يجب أن تحتوي على حرف واحد على الأقل"
    if not re.search(r"[0-9]", password):
        return False, "كلمة المرور يجب أن تحتوي على رقم واحد على الأقل"
    return True, ""


# ─── JWT Tokens ────────────────────────────────────────────────
def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
