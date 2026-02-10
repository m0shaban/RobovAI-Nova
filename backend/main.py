from fastapi import FastAPI, Request, HTTPException, File, UploadFile, Form
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import tempfile
import json
import uuid
import os
from backend.tools.registry import ToolRegistry
from backend.core.config import settings

# Setup Logger FIRST
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("robovai")

# ── Startup sanity check: verify critical packages are importable ──
_missing_pkgs = []
for _pkg in ["langchain_openai", "langchain_groq", "langchain_core", "langgraph"]:
    try:
        __import__(_pkg)
    except ImportError:
        _missing_pkgs.append(_pkg)
if _missing_pkgs:
    logger.error(
        f"❌ Missing packages: {', '.join(_missing_pkgs)}. "
        f"Python in use: {sys.executable}  —  "
        f"Make sure you're running with the venv: .venv/Scripts/python"
    )

# Initialize FastAPI app
app = FastAPI(
    title="RobovAI Backend",
    description="Universal AI Toolset Backend API",
    version="1.0.0",
)

# Register Tools on Startup
from backend.tools.loader import register_all_tools

register_all_tools()

# Initialize Telegram Bot (safe import)

# Initialize Telegram Bot (safe import)
try:
    from backend.telegram_bot import create_telegram_app

    telegram_app = create_telegram_app()
    if telegram_app:
        logger.info("✅ Telegram bot enabled")
    else:
        logger.info("⚠️ Telegram bot disabled (no token)")
except Exception as e:
    logger.error(f"Telegram bot init failed: {e}")
    telegram_app = None


@app.on_event("startup")
async def on_startup():
    """Run startup tasks"""
    if telegram_app:
        try:
            logger.info("⚙️ Initializing Telegram Bot Application...")
            await telegram_app.initialize()
            await telegram_app.start()
            logger.info("✅ Telegram Bot Initialized & Started")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Telegram Bot: {e}")

    # Auto-set Telegram Webhook if EXTERNAL_URL is set
    external_url = os.getenv("EXTERNAL_URL") or os.getenv("RENDER_EXTERNAL_URL")
    if external_url and telegram_app:
        webhook_url = f"{external_url}/telegram-webhook"
        logger.info(f"🚀 Setting Telegram webhook to: {webhook_url}")
        try:
            await telegram_app.bot.set_webhook(webhook_url)
            logger.info("✅ Telegram webhook set successfully")
        except Exception as e:
            logger.error(f"❌ Failed to set Telegram webhook: {e}")


@app.on_event("shutdown")
async def on_shutdown():
    """Run shutdown tasks"""
    if telegram_app:
        logger.info("🛑 Stopping Telegram Bot...")
        try:
            await telegram_app.stop()
            await telegram_app.shutdown()
            logger.info("✅ Telegram Bot Stopped")
        except Exception as e:
            logger.error(f"❌ Failed to stop Telegram Bot: {e}")


# ── CORS: restrict to known origins ──
_allowed_origins = [
    os.getenv("FRONTEND_URL", "https://robovai-nova.onrender.com"),
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rate Limiting ──
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded

    limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    _has_limiter = True
except ImportError:
    logger.warning(
        "⚠️ slowapi not installed — rate limiting disabled. Run: pip install slowapi"
    )
    _has_limiter = False

# Mount static files for uploads (presentations, files, etc.)
os.makedirs("uploads", exist_ok=True)
# (mounts registered later after route definitions)


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


@app.get("/favicon.ico")
async def favicon():
    """Serve favicon to avoid noisy 404s in browser console."""
    icon_path = Path(__file__).resolve().parent.parent / "favicon_io" / "favicon.ico"
    if icon_path.exists():
        return FileResponse(str(icon_path))
    raise HTTPException(status_code=404, detail="Not Found")


# Serve other top-level HTML files — allowlist to prevent path traversal
_ALLOWED_PAGES = {
    "chat",
    "signup",
    "login",
    "admin",
    "account",
    "settings",
    "developers",
    "index",
}


@app.get("/{page}.html")
async def serve_html_page(page: str):
    # Strip any path separators to block traversal
    safe_page = page.replace("/", "").replace("\\", "").replace("..", "")
    if safe_page not in _ALLOWED_PAGES:
        raise HTTPException(status_code=404, detail="Not Found")
    path = f"{safe_page}.html"
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="Not Found")


# (Duplicate mounts removed — using the ones registered above)


# ═══════════════════════════════════════════════════════════════════════════
# 🔐 AUTHENTICATION & SECURITY
# ═══════════════════════════════════════════════════════════════════════════
from fastapi import Depends, status, Response, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from backend.core.database import db_client
from backend.core.security import (
    create_access_token,
    decode_access_token,
    validate_password_strength,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str


async def get_current_user_from_cookie(request: Request):
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
        raise HTTPException(status_code=403, detail="⛔ صلاحيات المسؤول مطلوبة")
    return current_user


# ── Rate limiting helper: no-op decorator when slowapi is missing ──
def _rl(limit_str: str):
    """Return a slowapi limiter decorator or a no-op if slowapi is unavailable."""
    if _has_limiter:
        return limiter.limit(limit_str)

    def _noop(fn):
        return fn

    return _noop


@app.post("/auth/register")
@_rl("5/minute")
async def register(request: Request, user: UserCreate, response: Response):
    """Register a new user — account needs Telegram OTP verification."""
    logger.info(
        f"Register endpoint called for email={user.email} full_name={user.full_name}"
    )
    try:
        # Validate password strength
        valid, msg = validate_password_strength(user.password)
        if not valid:
            raise HTTPException(status_code=400, detail=msg)

        # Validate email format
        if "@" not in user.email or "." not in user.email:
            raise HTTPException(status_code=400, detail="البريد الإلكتروني غير صحيح")

        res = await db_client.create_user(user.email, user.password, user.full_name)
        logger.info(f"create_user returned: {res}")
        if not res:
            raise HTTPException(status_code=400, detail="البريد الإلكتروني مسجل بالفعل")

        # Generate OTP for Telegram verification
        import random as _rnd

        otp = str(_rnd.randint(100000, 999999))
        await db_client.store_otp(res["id"], otp, "telegram_verify", minutes=10)
        logger.info(f"OTP generated for user_id={res['id']}")

        # Return pending — user must verify via Telegram
        return {
            "status": "pending_verification",
            "message": "تم إنشاء الحساب! فعّل حسابك عبر تليجرام.",
            "user": res,
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception("Registration failed")
        return JSONResponse(
            status_code=500, content={"detail": "Internal Server Error"}
        )


@app.post("/auth/login")
@_rl("10/minute")
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """Login and set Session Cookie"""
    user = await db_client.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="البريد الإلكتروني أو كلمة المرور غير صحيحة",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if account is verified
    if not user.get("is_verified"):
        raise HTTPException(
            status_code=403,
            detail="الحساب غير مُفعّل. افتح بوت @robovainova_bot في تليجرام وأرسل /verify لتفعيل حسابك.",
        )

    access_token = create_access_token(data={"sub": user["email"]})

    # Store Session in DB
    expires_at = (datetime.now() + timedelta(days=1)).isoformat()
    await db_client.create_session(user["id"], access_token, expires_at)

    # Set Secure Cookie
    _is_production = os.getenv("RENDER") or os.getenv("ENVIRONMENT") == "production"
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=bool(_is_production),
        max_age=86400,  # 1 day
        samesite="lax",
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/auth/logout")
async def logout(response: Response, request: Request):
    """Logout and revoke session"""
    token = request.cookies.get("access_token")
    if token:
        if token.startswith("Bearer "):
            token = token.split(" ")[1]
        await db_client.delete_session(token)

    response.delete_cookie("access_token")
    return {"status": "success"}


@app.get("/auth/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """Get current user info including balance and role."""
    usage = await db_client.get_daily_usage(str(current_user["id"]))
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "username": current_user.get(
            "full_name", current_user.get("email", "").split("@")[0]
        ),
        "full_name": current_user.get("full_name", ""),
        "role": current_user.get("role", "user"),
        "balance": usage["balance"],
        "daily_used": usage["daily_used"],
        "daily_limit": usage["daily_limit"],
        "tier": usage["tier"],
    }


@app.post("/auth/settings")
async def save_user_settings(
    payload: Dict[str, Any], current_user: dict = Depends(get_current_user)
):
    """Save user preferences (best-effort, stored in user record)."""
    # This is optional server-side storage; primary settings are in localStorage
    return {"status": "success", "message": "Settings saved"}


@app.get("/user/balance")
async def get_user_balance(current_user: dict = Depends(get_current_user)):
    """Get current balance and usage stats."""
    usage = await db_client.get_daily_usage(str(current_user["id"]))
    return usage


@app.get("/user/usage-history")
async def get_usage_history(current_user: dict = Depends(get_current_user)):
    """Get recent usage history."""
    history = await db_client.get_usage_history(str(current_user["id"]))
    return {"status": "success", "history": history}


# ═══════════════════════════════════════════════════════════════════════════


# Webhook Endpoint (General)
class WebhookPayload(BaseModel):
    user_id: str
    message: str
    platform: str  # 'telegram', 'whatsapp', 'web'
    metadata: Optional[Dict[str, Any]] = None


@app.post("/webhook")
async def handle_webhook(
    payload: WebhookPayload,
    current_user: Optional[dict] = Depends(
        get_current_user
    ),  # Optional for now, strict later
):
    """
    Central entry point with SMART TOOL DETECTION.
    For Web Platform, it requires Authentication (current_user).
    For Webhooks (Telegram/WhatsApp), it relies on Platform Verification.
    """
    try:
        # Security Check for Web
        if payload.platform == "web":
            if not current_user:
                raise HTTPException(status_code=401, detail="Unauthorized Web Access")
            # Enforce real user_id
            payload.user_id = str(current_user["id"])

        logger.info(
            f"📨 Webhook received from {payload.user_id} [{payload.platform}]: {payload.message[:100]}"
        )

        user_id = payload.user_id
        message = payload.message.strip()

        # 1. SAVE USER MESSAGE 🧠
        # Only if it's a real integer ID (Web User)
        if payload.platform == "web":
            try:
                await db_client.save_message(int(user_id), "user", message)
            except Exception as e:
                logger.warning(f"Failed to save user message: {e}")

        # 2. ROUTE MESSAGE using SmartToolRouter 🚀
        response_text = ""

        try:
            from backend.core.smart_router import SmartToolRouter

            routing_result = await SmartToolRouter.route_message(
                message, user_id, platform=payload.platform
            )

            logger.info(f"Routing result: {routing_result['type']}")

            if routing_result["type"] == "tool":
                response_text = routing_result["result"].get("output", "تم التنفيذ ✅")
                logger.info(f"Tool executed: {routing_result.get('tool_name')}")
            elif routing_result["type"] == "error":
                response_text = (
                    f"❌ حدث خطأ: {routing_result.get('error', 'خطأ غير معروف')}"
                )
                logger.error(f"Tool error: {routing_result.get('error')}")
            else:
                # Chat mode - use LLM
                from backend.core.llm import llm_client

                # Get context if web
                context_str = ""
                if payload.platform == "web":
                    try:
                        history = await db_client.get_recent_messages(
                            int(user_id), limit=5
                        )
                        context_str = "\n".join(
                            [f"{msg['role']}: {msg['content']}" for msg in history]
                        )
                    except Exception as e:
                        logger.warning(f"Failed to get history: {e}")

                system_persona = """
                أنت نوفا (Nova)، مساعد ذكي متطور من تطوير RobovAI Solutions.
                - تتحدث باللهجة المصرية الودودة أو العربية الفصحى المبسطة.
                - أنت محترف، ذكي، وتتمتع بحس فكاهي خفيف.
                - هدفك مساعدة المستخدم في مهامه.
                - إذا لم تفهم، اطلب التوضيح بأدب.
                """

                prompt = (
                    f"Context:\n{context_str}\n\nUser: {message}"
                    if context_str
                    else message
                )
                response_text = await llm_client.generate(
                    prompt, system_prompt=system_persona
                )
                logger.info(f"LLM response generated for user {user_id}")

        except Exception as e:
            logger.error(f"Routing/LLM error: {e}", exc_info=True)
            response_text = "⚠️ عذراً، حدث خطأ تقني. يرجى المحاولة مرة أخرى."

        # 3. SAVE ASSISTANT RESPONSE 🧠
        if payload.platform == "web" and response_text:
            try:
                await db_client.save_message(int(user_id), "assistant", response_text)
            except Exception as e:
                logger.warning(f"Failed to save assistant message: {e}")

        logger.info(f"✅ Response sent to {user_id}")
        return {"status": "success", "response": response_text}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook critical error: {e}", exc_info=True)
        return {"status": "error", "response": "⚠️ حدث خطأ تقني. يرجى المحاولة لاحقاً."}


@app.post("/webhook_audio")
async def handle_audio_webhook(
    audio: UploadFile = File(...), user_id: str = Form(...), platform: str = Form(...)
):
    """
    نقطة نهاية لاستقبال ملفات الصوت من الواجهة
    """
    logger.info(f"Received audio file: {audio.filename}")

    try:
        # حفظ الملف مؤقتاً
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_path = temp_file.name

        # استدعاء أداة voice_note مع مسار الملف
        tool_class = ToolRegistry.get_tool("/voice_note")

        if tool_class:
            tool = tool_class()
            result = await tool.execute(temp_path, user_id)

            # حذف الملف المؤقت
            try:
                os.unlink(temp_path)
            except:
                pass

            response = result.get("output", "تم معالجة الصوت")
            return {"status": "success", "response": response, "output": response}
        else:
            try:
                os.unlink(temp_path)
            except:
                pass
            return {"status": "error", "message": "Voice tool not found"}

    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        return {"status": "error", "message": str(e), "response": f"❌ خطأ: {str(e)}"}


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...), current_user: dict = Depends(get_current_user)
):
    """
    Generic file upload for multimodal interactions (auth required)
    """
    try:
        # Limit file size to 20MB
        MAX_SIZE = 20 * 1024 * 1024
        content_peek = await file.read(MAX_SIZE + 1)
        if len(content_peek) > MAX_SIZE:
            raise HTTPException(
                status_code=413, detail="الملف كبير جداً — الحد الأقصى 20MB"
            )
        await file.seek(0)
        # Create uploads directory if it doesn't exist
        os.makedirs("uploads", exist_ok=True)

        # Save file with unique name
        ext = os.path.splitext(file.filename)[1]
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        filepath = os.path.join("uploads", filename)

        with open(filepath, "wb+") as buffer:
            content = await file.read()
            buffer.write(content)

        return {
            "status": "success",
            "filepath": os.path.abspath(filepath),
            "filename": filename,
            "url": f"/uploads/{filename}",
        }
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload_image")
async def upload_image_to_imgbb(
    file: UploadFile = File(...),
    user_id: str = Form("anonymous"),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload image directly to ImgBB and return direct URL
    """
    try:
        # Check if it's an image
        content_type = file.content_type or ""
        if not content_type.startswith("image/"):
            return {
                "status": "error",
                "message": "❌ الملف المرفوع ليس صورة",
                "response": "❌ يرجى رفع ملف صورة (jpg, png, gif, etc.)",
            }

        # Save temporarily
        os.makedirs("uploads", exist_ok=True)
        ext = os.path.splitext(file.filename)[1] or ".jpg"
        temp_filename = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
        temp_path = os.path.join("uploads", temp_filename)

        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        # Use ImgBB tool
        tool_class = ToolRegistry.get_tool("/imgbb")

        if tool_class:
            tool = tool_class()
            result = await tool.execute(temp_path, user_id)

            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass

            return {
                "status": "success",
                "response": result.get("output", "تم رفع الصورة"),
                "direct_url": result.get("direct_url"),
                "display_url": result.get("display_url"),
                "delete_url": result.get("delete_url"),
            }
        else:
            # Fallback: keep local file
            return {
                "status": "success",
                "response": f"📷 تم حفظ الصورة محلياً: {temp_filename}",
                "filepath": os.path.abspath(temp_path),
                "url": f"/uploads/{temp_filename}",
            }

    except Exception as e:
        logger.error(f"Image upload failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "response": f"❌ خطأ في رفع الصورة: {str(e)}",
        }


# Mount Public Assets & Uploads (single mount point)
try:
    app.mount("/public", StaticFiles(directory="public"), name="public")
except Exception:
    pass
try:
    app.mount("/static", StaticFiles(directory="public"), name="static")
except Exception:
    pass
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/")
async def serve_landing():
    return FileResponse("index.html")


@app.get("/chat")
async def serve_chat():
    return FileResponse("chat.html")


@app.get("/developers")
async def serve_developers():
    return FileResponse("developers.html")


@app.get("/login")
async def serve_login():
    return FileResponse("login.html")


@app.get("/signup")
async def serve_signup():
    return FileResponse("signup.html")


@app.get("/admin")
async def serve_admin():
    return FileResponse("admin.html")


@app.get("/tools")
async def get_tools():
    """
    Get all registered tools for dynamic frontend rendering
    """
    return {
        "status": "success",
        "tools": ToolRegistry.get_all_tools_info(),
        "grouped": ToolRegistry.get_tools_by_category(),
        "count": len(ToolRegistry.list_tools()),
    }


# ═══════════════════════════════════════════════════════════════════════════
# 📱 MULTI-PLATFORM WEBHOOKS
# ═══════════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════════
# (Old adapter-based telegram webhook removed — using telegram_app.process_update below)
# ═══════════════════════════════════════════════════════════════════════════


@app.post("/whatsapp_webhook")
async def whatsapp_webhook(request: Request):
    """
    WhatsApp Business API Webhook
    """
    try:
        from backend.adapters.platforms import WhatsAppAdapter, OutgoingMessage

        payload = await request.json()
        access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
        phone_id = os.getenv("WHATSAPP_PHONE_ID", "")

        if not access_token or not phone_id:
            logger.error("WhatsApp credentials not set")
            return {"status": "ok"}

        adapter = WhatsAppAdapter(access_token, phone_id)
        message = await adapter.parse_webhook(payload)

        if not message:
            return {"status": "ok"}

        # Route message
        from backend.core.smart_router import SmartToolRouter

        routing_result = await SmartToolRouter.route_message(
            message.text, message.user_id, platform="whatsapp"
        )

        # Get response
        if routing_result["type"] == "tool":
            response = routing_result["result"].get("output", "تم التنفيذ ✅")
        else:
            from backend.core.llm import llm_client

            response = await llm_client.generate(
                message.text,
                provider="auto",
                system_prompt="أنت RobovAI Nova Agent - مساعد ذكي مصري ودود. رد بالمصري العامي.",
            )

        # Send response
        await adapter.send_message(
            OutgoingMessage(text=response[:4000], chat_id=message.chat_id)
        )

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        return {"status": "ok"}


@app.get("/whatsapp_webhook")
async def whatsapp_verify(request: Request):
    """WhatsApp webhook verification"""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "robovai_verify")

    if mode == "subscribe" and token == verify_token:
        return int(challenge)

    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/messenger_webhook")
async def messenger_webhook(request: Request):
    """
    Facebook Messenger Webhook
    """
    try:
        from backend.adapters.platforms import MessengerAdapter, OutgoingMessage

        payload = await request.json()
        page_token = os.getenv("MESSENGER_PAGE_TOKEN", "")

        if not page_token:
            logger.error("MESSENGER_PAGE_TOKEN not set")
            return {"status": "ok"}

        adapter = MessengerAdapter(page_token)
        message = await adapter.parse_webhook(payload)

        if not message:
            return {"status": "ok"}

        # Send typing
        await adapter.send_typing(message.chat_id)

        # Route message
        from backend.core.smart_router import SmartToolRouter

        routing_result = await SmartToolRouter.route_message(
            message.text, message.user_id, platform="messenger"
        )

        # Get response
        if routing_result["type"] == "tool":
            response = routing_result["result"].get("output", "تم التنفيذ ✅")
        else:
            from backend.core.llm import llm_client

            response = await llm_client.generate(
                message.text,
                provider="auto",
                system_prompt="أنت RobovAI Nova Agent - مساعد ذكي مصري ودود. رد بالمصري العامي.",
            )

        # Send response
        await adapter.send_message(
            OutgoingMessage(
                text=response[:2000], chat_id=message.chat_id  # Messenger limit
            )
        )

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Messenger webhook error: {e}")
        return {"status": "ok"}


@app.get("/messenger_webhook")
async def messenger_verify(request: Request):
    """Messenger webhook verification"""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    verify_token = os.getenv("MESSENGER_VERIFY_TOKEN", "robovai_verify")

    if mode == "subscribe" and token == verify_token:
        return challenge

    raise HTTPException(status_code=403, detail="Verification failed")


@app.get("/user_stats/{user_id}")
async def get_user_stats(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get user usage statistics (auth required)"""
    from backend.core.smart_router import SmartToolRouter

    stats = SmartToolRouter.get_user_stats(user_id)
    return {"status": "success", "stats": stats}


# ═══════════════════════════════════════════════════════════════════════════
# 📱 TELEGRAM WEBHOOK
# ═══════════════════════════════════════════════════════════════════════════


@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    """Handle Telegram webhook updates"""
    if not telegram_app:
        raise HTTPException(status_code=503, detail="Telegram bot not configured")

    try:
        data = await request.json()
        from telegram import Update

        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════
# 💳 UNIFIED PAYMENT GATEWAY (Stripe + Paymob + LemonSqueezy)
# ═══════════════════════════════════════════════════════════════════════════

from backend.payment_gateway import PaymentGateway, PLANS, TOKEN_PACKAGES


@app.post("/payments/checkout")
async def create_checkout(
    plan: str = "pro",
    provider: str = "auto",
    method: str = "card",
    current_user: dict = Depends(get_current_user),
):
    """Create checkout URL with any configured payment provider."""
    if plan not in ["pro", "enterprise"]:
        raise HTTPException(status_code=400, detail="الباقة غير متاحة")

    result = await PaymentGateway.create_checkout(
        user_id=str(current_user.get("id")),
        user_email=current_user.get("email"),
        user_name=current_user.get("full_name", ""),
        plan=plan,
        provider=provider,
        method=method,
    )

    if not result.get("checkout_url"):
        raise HTTPException(
            status_code=503, detail=result.get("error", "خدمة الدفع غير متاحة")
        )

    return result


@app.post("/payments/buy-tokens")
async def buy_tokens(
    package_id: str = "tokens_500",
    provider: str = "auto",
    current_user: dict = Depends(get_current_user),
):
    """Buy token package (one-time purchase)."""
    if package_id not in TOKEN_PACKAGES:
        raise HTTPException(status_code=400, detail="الباكج غير متاح")

    result = await PaymentGateway.create_checkout(
        user_id=str(current_user.get("id")),
        user_email=current_user.get("email"),
        user_name=current_user.get("full_name", ""),
        provider=provider,
        is_token_package=True,
        package_id=package_id,
    )

    if not result.get("checkout_url"):
        raise HTTPException(
            status_code=503, detail=result.get("error", "خدمة الدفع غير متاحة")
        )

    return result


@app.post("/payments/webhook/{provider}")
async def payment_webhook(provider: str, request: Request):
    """Unified webhook handler — /payments/webhook/stripe|paymob|lemonsqueezy"""
    if provider not in ("stripe", "paymob", "lemonsqueezy"):
        raise HTTPException(status_code=400, detail="Unknown provider")

    raw_body = await request.body()

    data: Dict[str, Any] = {}
    # 1) Try JSON
    try:
        if raw_body:
            data = json.loads(raw_body)
    except Exception:
        data = {}

    # 2) Fallback: form-encoded (Paymob callbacks may hit here)
    if not data:
        try:
            form = await request.form()
            data = dict(form)
        except Exception:
            pass

    # 3) Always include query params (Paymob response callback can be GET with params)
    try:
        qp = dict(request.query_params)
        if qp:
            data = {**qp, **data}
    except Exception:
        pass

    headers = dict(request.headers)

    result = await PaymentGateway.handle_webhook(
        provider, data, raw_body, headers, db_client
    )

    if result.get("success"):
        logger.info(f"💰 Payment webhook [{provider}]: {result}")
        return {"status": "ok", **result}
    else:
        logger.warning(f"⚠️ Payment webhook [{provider}] failed: {result}")
        raise HTTPException(
            status_code=400, detail=result.get("error", "Webhook failed")
        )


# Keep old endpoint for backwards compatibility
@app.post("/payments/webhook")
async def legacy_webhook(request: Request):
    """Legacy webhook — auto-detect provider from headers."""
    headers = dict(request.headers)
    if "stripe-signature" in headers:
        return await payment_webhook("stripe", request)
    elif "x-signature" in headers:
        return await payment_webhook("lemonsqueezy", request)
    else:
        return await payment_webhook("paymob", request)


@app.get("/api/acceptance/post_pay")
async def paymob_post_pay_get(request: Request):
    """Paymob Transaction response callback (GET redirect after payment)."""
    params = dict(request.query_params)
    success = params.get("success", "false").lower() == "true"
    order_id = params.get("order", params.get("merchant_order_id", ""))
    txn_id = params.get("id", "")
    amount = params.get("amount_cents", "0")

    # Process payment if successful
    if success:
        hmac_val = params.get("hmac", "")
        if hmac_val:
            result = await PaymentGateway.handle_webhook(
                "paymob", params, b"", dict(request.headers), db_client
            )
            if result.get("success"):
                logger.info(
                    f"💰 Paymob post_pay success: order={order_id}, txn={txn_id}"
                )
        return RedirectResponse(url="/account?payment=success", status_code=303)
    else:
        logger.warning(f"⚠️ Paymob post_pay failed: order={order_id}")
        return RedirectResponse(url="/account?payment=failed", status_code=303)


@app.post("/api/acceptance/post_pay")
async def paymob_post_pay_post(request: Request):
    """Paymob Transaction response callback (POST)."""
    raw_body = await request.body()
    data: Dict[str, Any] = {}
    try:
        data = json.loads(raw_body) if raw_body else {}
    except Exception:
        try:
            form = await request.form()
            data = dict(form)
        except Exception:
            pass

    qp = dict(request.query_params)
    if qp:
        data = {**qp, **data}

    success = str(data.get("success", "false")).lower() == "true"

    if success:
        result = await PaymentGateway.handle_webhook(
            "paymob", data, raw_body, dict(request.headers), db_client
        )
        if result.get("success"):
            logger.info(f"💰 Paymob post_pay POST success: {result}")

    return RedirectResponse(
        url=f"/account?payment={'success' if success else 'failed'}", status_code=303
    )


@app.get("/payments/pricing")
async def get_pricing():
    """Get pricing tiers + available providers."""
    return {
        "plans": PLANS,
        "token_packages": TOKEN_PACKAGES,
        "providers": PaymentGateway.get_providers(),
    }


@app.get("/payments/subscription")
async def get_subscription(current_user: dict = Depends(get_current_user)):
    """Get user's current subscription."""
    usage = await db_client.get_daily_usage(str(current_user.get("id")))
    return {
        "tier": usage.get("tier", "free"),
        "balance": usage.get("balance", 0),
        "daily_used": usage.get("daily_used", 0),
        "daily_limit": usage.get("daily_limit", 50),
        "can_use": usage.get("can_use", False),
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "tools_count": len(ToolRegistry.list_tools()),
        "platforms": ["web", "telegram", "whatsapp", "messenger", "discord"],
    }


# ═══════════════════════════════════════════════════════════════════════════
# 🤖 AI AGENT ENDPOINTS (LangGraph)
# ═══════════════════════════════════════════════════════════════════════════


class AgentRequest(BaseModel):
    """Request model for agent endpoint"""

    message: str
    user_id: Optional[str] = "anonymous"
    platform: Optional[str] = "web"
    thread_id: Optional[str] = None
    use_agent: Optional[bool] = True  # If False, use SmartRouter instead
    ai_level: Optional[str] = "balanced"  # "fast", "balanced", "powerful"


@app.post("/agent/run")
async def run_agent_endpoint(
    request: AgentRequest,
    current_user: Optional[dict] = Depends(get_current_user_from_cookie),
):
    """
    🚀 Execute a task using the Nova AI Agent (LangGraph)

    This endpoint uses the advanced AI Agent for complex multi-step tasks.
    The agent can:
    - Analyze and plan complex tasks
    - Execute multiple tools in sequence
    - Retry on failures
    - Learn from context

    Use this for complex requests like:
    - "ارسم صورة قطة وترجم وصفها للفرنساوي"
    - "ابحث عن مصر في ويكيبيديا واحكيلي نكتة عنها"
    """
    try:
        # Use authenticated user ID if available
        user_id = str(current_user["id"]) if current_user else request.user_id

        logger.info(f"🤖 Agent request from {user_id}: {request.message[:50]}...")

        if request.use_agent:
            # Use the LangGraph Agent
            from backend.agent.graph import run_agent

            result = await run_agent(
                message=request.message, user_id=user_id, platform=request.platform
            )

            logger.info(f"✅ Agent completed. Success: {result.get('success')}")

            return {
                "status": "success" if result.get("success") else "error",
                "response": result.get("final_answer", "تم!"),
                "tool_results": result.get("tool_results", []),
                "plan": result.get("plan", []),
                "phase": result.get("phase"),
                "errors": result.get("errors", []),
            }
        else:
            # Fallback to SmartRouter for simple tasks
            from backend.core.smart_router import SmartToolRouter

            routing_result = await SmartToolRouter.route_message(
                request.message, user_id, platform=request.platform
            )

            if routing_result["type"] == "tool":
                response = routing_result["result"].get("output", "تم التنفيذ ✅")
            else:
                from backend.core.llm import llm_client

                response = await llm_client.generate(
                    request.message, system_prompt="أنت نوفا، مساعد ذكي من RobovAI."
                )

            return {"status": "success", "response": response}

    except Exception as e:
        logger.error(f"❌ Agent error: {e}", exc_info=True)
        return {"status": "error", "response": f"❌ حدث خطأ: {str(e)}", "error": str(e)}


@app.post("/agent/stream")
async def stream_agent_endpoint(request: AgentRequest):
    """
    🔄 Stream agent execution step by step (POST version)

    Returns Server-Sent Events for real-time updates.
    """
    return await _stream_agent(request.message, request.user_id, request.platform)


@app.get("/agent/stream")
async def stream_agent_get(
    message: str,
    user_id: str = "web_user",
    platform: str = "web",
    ai_level: str = "balanced",
    request: Request = None,
):
    """
    🔄 Stream agent execution (GET for EventSource).
    Authenticates via cookie, deducts 1 token per request.
    Uses response cache to save tokens on repeated/greeting messages.
    ai_level: "fast" (chatbot only), "balanced" (smart routing), "powerful" (full agent)
    """
    from backend.cache import get_cached, set_cached, get_instant_response
    from fastapi.responses import StreamingResponse as _SR

    # — Check instant / cached response FIRST (zero tokens) —
    instant = get_instant_response(message)
    if instant:

        async def _instant():
            yield f"event: completed\ndata: {json.dumps({'final_answer': instant}, ensure_ascii=False)}\n\n"
            yield f"event: done\ndata: {json.dumps({'done': True})}\n\n"

        return _SR(_instant(), media_type="text/event-stream")

    # Try to authenticate from cookie
    real_user_id = user_id
    if request:
        user = await get_current_user_from_cookie(request)
        if user:
            real_user_id = str(user["id"])
            # Check balance before running
            usage = await db_client.get_daily_usage(real_user_id)
            if not usage["can_use"]:

                async def _no_balance():
                    yield f'event: error\ndata: {json.dumps({"error": "رصيدك غير كافي. يرجى شراء توكنز إضافية أو ترقية الباقة."}, ensure_ascii=False)}\n\n'

                return _SR(_no_balance(), media_type="text/event-stream")

            # Check LLM cache before deducting
            cached = get_cached(message, real_user_id)
            if cached:

                async def _cached():
                    yield f"event: completed\ndata: {json.dumps({'final_answer': cached, 'cached': True}, ensure_ascii=False)}\n\n"
                    yield f"event: done\ndata: {json.dumps({'done': True})}\n\n"

                return _SR(_cached(), media_type="text/event-stream")

            # Deduct 1 token for the request
            await db_client.deduct_tokens(real_user_id, 1, "agent_chat")

    # ── AI level routing: fast = chatbot, balanced = smart, powerful = full agent ──
    if ai_level == "fast":
        # Fast mode: Use only LLM chatbot (no tools/agent)
        return await _stream_chatbot(message, real_user_id, platform)

    if ai_level == "balanced":
        # Balanced: Use smart router to decide chat vs tool vs agent
        from backend.core.smart_router import SmartToolRouter

        routing = await SmartToolRouter.route(message, real_user_id, platform)
        if routing.route_type == "chat":
            return await _stream_chatbot(message, real_user_id, platform)
        # Otherwise fall through to full agent

    return await _stream_agent(message, real_user_id, platform)


async def _stream_chatbot(message: str, user_id: str, platform: str):
    """Fast chatbot mode — LLM only, no tools/agent. Much faster responses."""
    from fastapi.responses import StreamingResponse
    import json

    async def event_generator():
        try:
            yield f"event: started\ndata: {json.dumps({'message': 'جاري الرد...'}, ensure_ascii=False)}\n\n"
            yield f"event: thinking\ndata: {json.dumps({'message': '🧠 جاري التفكير...'}, ensure_ascii=False)}\n\n"

            from backend.core.llm import llm_client

            # Get conversation context
            context_str = ""
            try:
                history = await db_client.get_recent_messages(int(user_id), limit=5)
                context_str = "\n".join(
                    [f"{msg['role']}: {msg['content']}" for msg in history]
                )
            except Exception:
                pass

            system_prompt = """أنت نوفا (Nova) — مساعد ذكي ودود من RobovAI Solutions.
تتكلم باللهجة المصرية أو الإنجليزية حسب لغة المستخدم.
أسلوبك: محترف، ذكي، مختصر، ومنظم.
تستخدم Markdown للتنسيق (عناوين، قوائم، bold، code blocks).
لو حد سألك عن نفسك: أنت نوفا عندك 99+ أداة ذكية.
ما تقترحش أدوات هنا — فقط رد كشات بوت ذكي."""

            prompt = (
                f"Context:\n{context_str}\n\nUser: {message}"
                if context_str
                else message
            )
            response = await llm_client.generate(prompt, system_prompt=system_prompt)

            # Cache it
            try:
                from backend.cache import set_cached

                set_cached(message, response, user_id, ttl=300)
            except Exception:
                pass

            yield f"event: completed\ndata: {json.dumps({'final_answer': response}, ensure_ascii=False)}\n\n"
            yield f"event: done\ndata: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            logger.error(f"Chatbot stream error: {e}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _stream_agent(message: str, user_id: str, platform: str):
    """Internal streaming function used by both GET and POST endpoints"""
    from fastapi.responses import StreamingResponse
    import json

    async def event_generator():
        try:
            from backend.agent.graph import NovaAgent
            import asyncio
        except ImportError as imp_err:
            logger.error(
                f"❌ Agent import failed: {imp_err}  — Python: {sys.executable}"
            )
            yield f"event: error\ndata: {json.dumps({'error': f'Server misconfiguration: {imp_err}. Restart with .venv Python.'}, ensure_ascii=False)}\n\n"
            return

        try:
            logger.info(f"🎬 Starting stream for: {message[:50]}...")

            # Send start event
            yield f"event: started\ndata: {json.dumps({'message': 'بدأ التنفيذ...'}, ensure_ascii=False)}\n\n"

            agent = NovaAgent(use_persistence=False)
            last_phase = None

            # Create iterator for the stream
            iterator = agent.stream(
                message, user_id=user_id, platform=platform
            ).__aiter__()

            # Task based iteration to support non-cancelling heartbeats
            next_item_task = asyncio.create_task(iterator.__anext__())

            while True:
                try:
                    done, pending = await asyncio.wait(
                        [next_item_task],
                        timeout=5.0,
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                    if next_item_task in done:
                        try:
                            state = next_item_task.result()
                            # Queue next item immediately
                            next_item_task = asyncio.create_task(iterator.__anext__())

                            # Send state update
                            for node_name, node_state in state.items():
                                if not isinstance(node_state, dict):
                                    continue

                                phase = node_state.get("phase", "unknown")
                                phase_upper = phase.upper() if phase else "UNKNOWN"

                                # Only send if phase changed
                                if phase != last_phase:
                                    last_phase = phase

                                    if phase_upper == "THINKING":
                                        yield f"event: thinking\ndata: {json.dumps({'message': '🧠 جاري التفكير...'}, ensure_ascii=False)}\n\n"

                                    elif phase_upper == "PLANNING":
                                        plan = node_state.get("plan_steps", [])
                                        yield f"event: planning\ndata: {json.dumps({'plan': plan, 'message': '📋 تم وضع الخطة'}, ensure_ascii=False)}\n\n"

                                    elif phase_upper == "ACTING":
                                        current_step = node_state.get(
                                            "current_step_index", 0
                                        )
                                        plan_steps = node_state.get("plan_steps", [])
                                        if current_step < len(plan_steps):
                                            step = plan_steps[current_step]
                                            yield f"event: executing\ndata: {json.dumps({'step': step, 'index': current_step + 1, 'total': len(plan_steps)}, ensure_ascii=False)}\n\n"

                                    elif phase_upper == "OBSERVING":
                                        yield f"event: observing\ndata: {json.dumps({'message': '👁️ جاري المراجعة...'}, ensure_ascii=False)}\n\n"

                                    elif phase_upper == "REFLECTING":
                                        yield f"event: reflecting\ndata: {json.dumps({'message': '🔄 جاري التحقق...'}, ensure_ascii=False)}\n\n"

                                    elif phase_upper == "COMPLETED":
                                        final_answer = node_state.get(
                                            "final_answer", "تم!"
                                        )
                                        tool_results = node_state.get(
                                            "tool_results", []
                                        )
                                        yield f"event: completed\ndata: {json.dumps({'final_answer': final_answer, 'tool_count': len(tool_results)}, ensure_ascii=False)}\n\n"

                                        # Cache the response for future identical queries
                                        try:
                                            from backend.cache import set_cached

                                            set_cached(message, final_answer, user_id)
                                        except Exception:
                                            pass

                        except StopAsyncIteration:
                            break
                        except Exception as e:
                            logger.error(f"Stream logic error: {e}")
                            break
                    else:
                        # Timeout - send heartbeat without cancelling
                        yield f": keep-alive\n\n"
                        continue

                except Exception as e:
                    logger.error(f"Event loop error: {e}")
                    break

            yield f"event: done\ndata: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"
            logger.info("✅ Stream completed successfully")

        except Exception as e:
            logger.error(f"❌ Stream error: {e}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/agent/state/{thread_id}")
async def get_agent_state(thread_id: str):
    """
    📊 Get the current state of an agent thread

    Useful for Human-in-the-loop scenarios.
    """
    try:
        from backend.agent.graph import get_agent

        agent = get_agent()
        state = agent.get_state(thread_id)

        if state:
            return {"status": "success", "state": dict(state)}
        else:
            return {"status": "not_found", "message": "Thread not found"}

    except Exception as e:
        return {"status": "error", "error": str(e)}


# ═══════════════════════════════════════════════════════════════
# 📜 HISTORY ENDPOINTS
# ═══════════════════════════════════════════════════════════════


@app.get("/history/conversations")
async def list_conversations(
    user_id: str = "default", current_user: dict = Depends(get_current_user)
):
    """قائمة محادثات المستخدم"""
    try:
        from backend.history.manager import get_conversation_manager

        manager = get_conversation_manager()
        conversations = manager.list_conversations(user_id)
        return {"status": "success", "conversations": conversations}
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        return {"status": "error", "error": str(e)}


@app.get("/history/conversation/{conv_id}")
async def get_conversation(
    conv_id: str,
    user_id: str = "default",
    current_user: dict = Depends(get_current_user),
):
    """الحصول على محادثة"""
    try:
        from backend.history.manager import get_conversation_manager
        from dataclasses import asdict

        manager = get_conversation_manager()
        conv = manager.get_conversation(user_id, conv_id)
        if conv:
            return {"status": "success", "conversation": asdict(conv)}
        return {"status": "not_found"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/history/conversation")
async def create_conversation(
    user_id: str = "default",
    title: str = "محادثة جديدة",
    current_user: dict = Depends(get_current_user),
):
    """إنشاء محادثة جديدة"""
    try:
        from backend.history.manager import get_conversation_manager
        from dataclasses import asdict

        manager = get_conversation_manager()
        conv = manager.create_conversation(user_id, title)
        return {
            "status": "success",
            "conversation": {"id": conv.id, "title": conv.title},
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/history/message")
async def add_message(
    conv_id: str,
    role: str,
    content: str,
    user_id: str = "default",
    current_user: dict = Depends(get_current_user),
):
    """إضافة رسالة"""
    try:
        from backend.history.manager import get_conversation_manager

        manager = get_conversation_manager()
        msg = manager.add_message(user_id, conv_id, role, content)
        return {"status": "success", "message_id": msg.id}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/history/search")
async def search_conversations(
    user_id: str,
    query: str,
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
):
    """بحث في المحادثات"""
    try:
        from backend.history.manager import get_conversation_manager

        manager = get_conversation_manager()
        results = manager.search_conversations(user_id, query, limit)
        return {"status": "success", "results": results}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.delete("/history/conversation/{conv_id}")
async def delete_conversation(
    conv_id: str,
    user_id: str = "default",
    current_user: dict = Depends(get_current_user),
):
    """حذف محادثة"""
    try:
        from backend.history.manager import get_conversation_manager

        manager = get_conversation_manager()
        deleted = manager.delete_conversation(user_id, conv_id)
        return {"status": "success" if deleted else "not_found"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/history/export/{conv_id}")
async def export_conversation(
    conv_id: str,
    user_id: str = "default",
    format: str = "json",
    current_user: dict = Depends(get_current_user),
):
    """تصدير محادثة"""
    try:
        from backend.history.manager import get_conversation_manager

        manager = get_conversation_manager()
        content = manager.export_conversation(user_id, conv_id, format)
        if content:
            return {"status": "success", "content": content, "format": format}
        return {"status": "not_found"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ═══════════════════════════════════════════════════════════════
# 📊 ADMIN & ANALYTICS ENDPOINTS
# ═══════════════════════════════════════════════════════════════


@app.get("/admin/stats")
async def get_admin_stats(admin: dict = Depends(require_admin)):
    """إحصائيات لوحة التحكم — للمسؤولين فقط"""
    try:
        tools = ToolRegistry.list_tools()
        db_stats = await db_client.get_stats()

        tool_stats = {"total": len(tools), "by_category": {}}
        for tool_name in tools:
            try:
                tool_cls = ToolRegistry.get_tool(tool_name)
                if tool_cls:
                    category = getattr(tool_cls, "category", "other")
                    tool_stats["by_category"][category] = (
                        tool_stats["by_category"].get(category, 0) + 1
                    )
            except:
                pass

        return {
            "status": "success",
            "stats": {
                "tools": tool_stats,
                "users": db_stats,
                "system": {
                    "uptime": "running",
                    "version": "3.0.0",
                    "agent": "Nova Multi-Agent",
                },
            },
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/admin/tools")
async def get_tools_detailed(admin: dict = Depends(require_admin)):
    """قائمة الأدوات مع التفاصيل — للمسؤولين فقط"""
    try:
        tools = ToolRegistry.list_tools()
        detailed = []

        for tool_name in tools:
            try:
                tool_cls = ToolRegistry.get_tool(tool_name)
                if tool_cls:
                    detailed.append(
                        {
                            "name": tool_name,
                            "description": getattr(tool_cls, "description", ""),
                            "category": getattr(tool_cls, "category", "other"),
                            "enabled": True,
                        }
                    )
            except:
                pass

        return {"status": "success", "tools": detailed, "total": len(detailed)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/admin/memory/{user_id}")
async def get_user_memory(user_id: str, admin: dict = Depends(require_admin)):
    """الحصول على ذاكرة المستخدم — للمسؤولين فقط"""
    try:
        from backend.agent.memory import get_memory_manager

        manager = get_memory_manager()
        context = manager.get_context(user_id, f"session_{user_id}")
        return {"status": "success", "memory": context}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/admin/users")
async def get_admin_users(admin: dict = Depends(require_admin)):
    """قائمة المستخدمين — للمسؤولين فقط"""
    try:
        users = await db_client.get_all_users()
        return {"status": "success", "users": users, "total": len(users)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/admin/set-role")
async def set_user_role(user_id: int, role: str, admin: dict = Depends(require_admin)):
    """تغيير صلاحية مستخدم — للمسؤولين فقط"""
    if role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Role must be 'user' or 'admin'")
    ok = await db_client.update_user_role(user_id, role)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "success", "message": f"User {user_id} role set to {role}"}


@app.post("/admin/add-tokens")
async def admin_add_tokens(
    user_id: int, amount: int, admin: dict = Depends(require_admin)
):
    """إضافة توكنز لمستخدم — للمسؤولين فقط"""
    ok = await db_client.add_tokens(str(user_id), amount)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "success", "message": f"Added {amount} tokens to user {user_id}"}


@app.get("/admin/logs")
async def get_system_logs(limit: int = 50, admin: dict = Depends(require_admin)):
    """الحصول على آخر السجلات — للمسؤولين فقط"""
    try:
        logs = []
        log_file = Path("logs/robovai.log")

        if log_file.exists():
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                logs = lines[-limit:]

        return {"status": "success", "logs": logs}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════
# 💳 SUBSCRIPTION & ACCOUNT MANAGEMENT ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════


class SubscriptionRequest(BaseModel):
    tier: str  # "free", "pro", "enterprise"


@app.get("/account/subscription")
async def get_subscription(current_user: dict = Depends(get_current_user)):
    """Get user subscription details"""
    usage = await db_client.get_daily_usage(str(current_user["id"]))
    history = await db_client.get_usage_history(str(current_user["id"]), limit=10)

    tier_info = {
        "free": {
            "name": "مجاني",
            "price": 0,
            "daily_limit": 50,
            "features": ["50 رسالة يومياً", "أدوات أساسية", "دعم عام"],
        },
        "pro": {
            "name": "Pro ⭐",
            "price": 99,
            "daily_limit": 500,
            "features": ["500 رسالة يومياً", "كل الأدوات", "أولوية عالية", "دعم مميز"],
        },
        "enterprise": {
            "name": "Enterprise 🏢",
            "price": 299,
            "daily_limit": -1,
            "features": [
                "رسائل غير محدودة",
                "كل الأدوات",
                "API مخصص",
                "دعم 24/7",
                "Custom Bot",
            ],
        },
    }

    current_tier = current_user.get("subscription_tier", "free") or "free"

    return {
        "status": "success",
        "subscription": {
            "tier": current_tier,
            "tier_info": tier_info.get(current_tier, tier_info["free"]),
            "balance": usage["balance"],
            "daily_used": usage["daily_used"],
            "daily_limit": usage["daily_limit"],
            "can_use": usage["can_use"],
        },
        "available_plans": tier_info,
        "usage_history": history,
    }


# ── Wallet Payment Helper ──────────────────────────────────────────────
async def _process_wallet_payment(payment_token: str, phone_number: str) -> dict:
    """Process Paymob mobile wallet payment (server-side POST)."""
    import httpx

    # Clean phone number — Paymob expects Egyptian local format: 01xxxxxxxxx
    phone = phone_number.strip().replace(" ", "").replace("-", "").replace("+", "")
    # Remove country code if present
    if phone.startswith("20") and len(phone) == 12:
        phone = "0" + phone[2:]  # 201xxxxxxxxx → 01xxxxxxxxx
    elif phone.startswith("2") and len(phone) == 11 and not phone.startswith("01"):
        phone = "0" + phone[1:]  # 21xxxxxxxxx → 01xxxxxxxxx
    # Ensure starts with 01
    if not phone.startswith("01") or len(phone) != 11:
        logger.warning(
            f"Invalid wallet phone format: {phone} (original: {phone_number})"
        )
        return {
            "status": "error",
            "detail": f"رقم الهاتف غير صحيح. يجب أن يكون بصيغة 01xxxxxxxxx (11 رقم)",
        }

    logger.info(
        f"💳 Wallet payment: phone={phone}, token_prefix={payment_token[:20]}..."
    )

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://accept.paymob.com/api/acceptance/payments/pay",
                headers={"Content-Type": "application/json"},
                json={
                    "source": {
                        "identifier": phone,
                        "subtype": "WALLET",
                    },
                    "payment_token": payment_token,
                },
            )
            data = resp.json()
            logger.info(f"💳 Wallet response status={resp.status_code}, body={data}")

            if resp.status_code in (200, 201):
                # Paymob returns redirect_url for wallet confirmation
                redirect_url = (
                    data.get("redirect_url")
                    or data.get("iframe_redirection_url")
                    or data.get("redirection_url")
                )
                if redirect_url:
                    return {
                        "status": "success",
                        "checkout_url": redirect_url,
                        "provider": "paymob",
                        "payment_type": "wallet",
                    }
                # Some wallets send push notification to phone directly
                return {
                    "status": "success",
                    "message": "تم إرسال طلب الدفع لهاتفك. افتح تطبيق المحفظة لتأكيد الدفع.",
                    "provider": "paymob",
                    "payment_type": "wallet_pending",
                }
            else:
                error_msg = data.get("message") or data.get("detail") or str(data)
                logger.error(f"Wallet payment failed [{resp.status_code}]: {error_msg}")
                return {
                    "status": "error",
                    "detail": f"فشل الدفع بالمحفظة: {error_msg}",
                }
    except Exception as e:
        logger.error(f"Wallet payment error: {e}")
        return {"status": "error", "detail": "خطأ في الاتصال بخدمة الدفع"}


@app.post("/account/buy-tokens")
async def account_buy_tokens(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Buy additional tokens via Paymob."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    package_id = body.get("package_id", "tokens_500")
    method = body.get("method", "card")
    phone_number = body.get("phone_number", "")

    if package_id not in TOKEN_PACKAGES:
        raise HTTPException(status_code=400, detail="الباكج غير متاح")

    result = await PaymentGateway.create_checkout(
        user_id=str(current_user.get("id")),
        user_email=current_user.get("email"),
        user_name=current_user.get("full_name", ""),
        provider="paymob",
        method=method,
        is_token_package=True,
        package_id=package_id,
    )

    if not result.get("checkout_url"):
        raise HTTPException(
            status_code=503, detail=result.get("error", "خدمة الدفع غير متاحة حالياً")
        )

    # Handle wallet payment (needs server-side POST to Paymob)
    checkout_url = result["checkout_url"]
    if checkout_url.startswith("WALLET_PAY:"):
        payment_token = checkout_url.replace("WALLET_PAY:", "")
        if not phone_number:
            raise HTTPException(
                status_code=400, detail="رقم الهاتف مطلوب للدفع بالمحفظة"
            )
        wallet_result = await _process_wallet_payment(payment_token, phone_number)
        return wallet_result

    return {"status": "success", **result}


@app.post("/account/subscribe")
async def account_subscribe(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Subscribe to a plan via Paymob."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    plan = body.get("plan", "pro")
    method = body.get("method", "card")  # "card" or "wallet"
    phone_number = body.get("phone_number", "")

    if plan not in ["pro", "enterprise"]:
        raise HTTPException(status_code=400, detail="الباقة غير متاحة")

    current_tier = current_user.get("subscription_tier", "free") or "free"
    if current_tier == plan:
        raise HTTPException(status_code=400, detail="أنت مشترك بالفعل في هذه الباقة")

    result = await PaymentGateway.create_checkout(
        user_id=str(current_user.get("id")),
        user_email=current_user.get("email"),
        user_name=current_user.get("full_name", ""),
        plan=plan,
        provider="paymob",
        method=method,
    )

    if not result.get("checkout_url"):
        raise HTTPException(
            status_code=503, detail=result.get("error", "خدمة الدفع غير متاحة حالياً")
        )

    # Handle wallet payment (needs server-side POST to Paymob)
    checkout_url = result["checkout_url"]
    if checkout_url.startswith("WALLET_PAY:"):
        payment_token = checkout_url.replace("WALLET_PAY:", "")
        if not phone_number:
            raise HTTPException(
                status_code=400, detail="رقم الهاتف مطلوب للدفع بالمحفظة"
            )
        wallet_result = await _process_wallet_payment(payment_token, phone_number)
        return wallet_result

    return {"status": "success", **result}


@app.get("/account/profile")
async def get_full_profile(current_user: dict = Depends(get_current_user)):
    """Full user profile with all settings"""
    usage = await db_client.get_daily_usage(str(current_user["id"]))
    return {
        "status": "success",
        "profile": {
            "id": current_user["id"],
            "email": current_user["email"],
            "full_name": current_user.get("full_name", ""),
            "role": current_user.get("role", "user"),
            "tier": current_user.get("subscription_tier", "free") or "free",
            "balance": usage["balance"],
            "daily_used": usage["daily_used"],
            "daily_limit": usage["daily_limit"],
            "created_at": current_user.get("created_at", ""),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# 📩 TELEGRAM OTP VERIFICATION
# ═══════════════════════════════════════════════════════════════════════════

import random as _random


class OTPRequest(BaseModel):
    email: str


class OTPVerify(BaseModel):
    email: str
    code: str


@app.post("/auth/request-otp")
@_rl("5/minute")
async def request_telegram_otp(request: Request, req: OTPRequest):
    """Generate OTP for a registered-but-unverified user.
    The user then opens @robovainova_bot → /verify → receives the code."""
    email = req.email.strip().lower()
    user = await db_client.get_user_by_email_unverified(email)
    if not user:
        raise HTTPException(
            status_code=404, detail="لم يتم العثور على حساب بهذا البريد"
        )

    if user.get("is_verified"):
        return {"status": "already_verified", "message": "الحساب مفعّل بالفعل ✅"}

    # Generate and store OTP
    otp = str(_random.randint(100000, 999999))
    await db_client.store_otp(user["id"], otp, "telegram_verify", minutes=10)

    return {
        "status": "success",
        "message": "تم إنشاء كود التحقق. افتح بوت RobovAI في تليجرام وأرسل /verify",
    }


@app.post("/auth/verify-otp")
@_rl("10/minute")
async def verify_otp_endpoint(request: Request, req: OTPVerify):
    """Verify OTP code and activate the account."""
    email = req.email.strip().lower()
    user = await db_client.get_user_by_email_unverified(email)
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")

    if user.get("is_verified"):
        return {"status": "already_verified", "message": "الحساب مفعّل بالفعل ✅"}

    valid = await db_client.verify_otp(user["id"], req.code, "telegram_verify")
    if not valid:
        raise HTTPException(
            status_code=400, detail="كود التحقق غير صحيح أو منتهي الصلاحية"
        )

    await db_client.set_user_verified(user["id"])

    # Auto-login after verification
    from backend.core.security import create_access_token

    access_token = create_access_token(data={"sub": email})
    expires_at = (datetime.now() + timedelta(days=1)).isoformat()
    await db_client.create_session(user["id"], access_token, expires_at)

    return {
        "status": "success",
        "message": "تم تفعيل الحساب بنجاح! ✅",
        "access_token": access_token,
        "user": {
            "id": user["id"],
            "email": email,
            "full_name": user.get("full_name", ""),
        },
    }


@app.get("/auth/check-verified")
async def check_verified(email: str):
    """Check if a user's account is verified (used for polling from signup page)."""
    user = await db_client.get_user_by_email_unverified(email.strip().lower())
    if not user:
        raise HTTPException(status_code=404, detail="المستخدم غير موجود")
    return {"verified": bool(user.get("is_verified"))}


# ═══════════════════════════════════════════════════════════════════════════
# 📄 SERVE ACCOUNT PAGE
# ═══════════════════════════════════════════════════════════════════════════


@app.get("/account")
async def serve_account():
    return FileResponse("account.html")


# ═══════════════════════════════════════════════════════════════════════════
# 🤖 CUSTOM BOT BUILDER
# ═══════════════════════════════════════════════════════════════════════════


class CustomBotCreate(BaseModel):
    name: str
    description: str = ""
    system_prompt: str
    avatar_emoji: str = "🤖"
    tools: list = []
    greeting: str = "مرحباً! كيف أقدر أساعدك?"


@app.post("/bots/create")
async def create_custom_bot(
    bot: CustomBotCreate, current_user: dict = Depends(get_current_user)
):
    """Create a custom bot with a specific persona and tools."""
    try:
        bot_id = str(uuid.uuid4())[:8]
        await db_client.execute(
            """INSERT OR REPLACE INTO custom_bots (id, user_id, name, description, system_prompt, avatar_emoji, tools, greeting, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                bot_id,
                str(current_user["id"]),
                bot.name,
                bot.description,
                bot.system_prompt,
                bot.avatar_emoji,
                json.dumps(bot.tools),
                bot.greeting,
                datetime.now().isoformat(),
            ),
        )
        return {
            "status": "success",
            "bot_id": bot_id,
            "message": f"تم إنشاء البوت '{bot.name}' بنجاح! 🎉",
        }
    except Exception as e:
        logger.error(f"Failed to create bot: {e}")
        raise HTTPException(status_code=500, detail="حدث خطأ أثناء إنشاء البوت")


@app.get("/bots/list")
async def list_custom_bots(current_user: dict = Depends(get_current_user)):
    """List user's custom bots."""
    try:
        bots = await db_client.execute(
            "SELECT id, name, description, avatar_emoji, greeting, created_at FROM custom_bots WHERE user_id = ? ORDER BY created_at DESC",
            (str(current_user["id"]),),
        )
        return {"status": "success", "bots": bots or []}
    except Exception as e:
        return {"status": "success", "bots": []}


@app.delete("/bots/{bot_id}")
async def delete_custom_bot(
    bot_id: str, current_user: dict = Depends(get_current_user)
):
    """Delete a custom bot."""
    await db_client.execute(
        "DELETE FROM custom_bots WHERE id = ? AND user_id = ?",
        (bot_id, str(current_user["id"])),
    )
    return {"status": "success", "message": "تم حذف البوت"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
