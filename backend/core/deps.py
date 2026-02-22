"""
🔐 Auth Dependencies — RobovAI Nova
═══════════════════════════════════════════
Shared FastAPI dependencies for authentication.
Extracted to avoid circular imports between main.py and sub-routers.
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from backend.core.database import db_client
from backend.core.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user_from_cookie(request: Request):
    """Extract and validate user from the access_token cookie."""
    token = request.cookies.get("access_token")
    if not token:
        return None

    # Remove 'Bearer ' prefix if present
    if token.startswith("Bearer "):
        token = token.split(" ")[1]

    # Check Session in DB (Server-Side Revocation)
    session = await db_client.get_session(token)
    if not session:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    user = await db_client.get_user_by_email(payload.get("sub"))
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme), request: Request = None
):
    """
    Robust Auth Dependency:
    1. Checks Authorization Header (Bearer Token)
    2. Checks 'access_token' Cookie
    3. Validates against Active Sessions DB
    """
    # 1. Try Token from Header
    if not token and request:
        token = request.cookies.get("access_token")
        if token and token.startswith("Bearer "):
            token = token.split(" ")[1]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check Session (Revocation Check)
    session = await db_client.get_session(token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await db_client.get_user_by_email(payload.get("sub"))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def require_admin(current_user: dict = Depends(get_current_user)):
    """Dependency that requires admin role."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges are required")
    return current_user
