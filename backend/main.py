from fastapi import FastAPI, Request, HTTPException, File, UploadFile, Form
import os
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
import os
from backend.tools.registry import ToolRegistry
from backend.core.config import settings

# Setup Logger FIRST
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("robovai")

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


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


@app.get("/")
async def root():
    """Serve landing page"""
    return FileResponse("index.html")


# Serve other top-level HTML files (e.g., chat.html, signup.html)
@app.get("/{page}.html")
async def serve_html_page(page: str):
    path = f"{page}.html"
    if os.path.exists(path):
        return FileResponse(path)
    raise HTTPException(status_code=404, detail="Not Found")


# Mount uploads and public assets
try:
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
except Exception:
    pass
try:
    app.mount("/public", StaticFiles(directory="public"), name="public")
except Exception:
    pass


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# ═══════════════════════════════════════════════════════════════════════════
# 🔐 AUTHENTICATION & SECURITY
# ═══════════════════════════════════════════════════════════════════════════
from fastapi import Depends, status, Response, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from backend.core.database import db_client
from backend.core.security import create_access_token, decode_access_token

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


@app.post("/auth/register")
async def register(user: UserCreate, response: Response):
    """Register and Auto-Login"""
    logger.info(
        f"Register endpoint called for email={user.email} full_name={user.full_name}"
    )
    try:
        res = await db_client.create_user(user.email, user.password, user.full_name)
        logger.info(f"create_user returned: {res}")
        if not res:
            raise HTTPException(status_code=400, detail="البريد الإلكتروني مسجل بالفعل")

        # Auto-login: Create Token
        access_token = create_access_token(data={"sub": user.email})
        logger.info(f"access token generated for email={user.email}")

        # Store Session
        expires_at = (datetime.now() + timedelta(days=1)).isoformat()
        await db_client.create_session(res["id"], access_token, expires_at)
        logger.info(f"session created for user_id={res['id']}")

        # Set Cookie
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=86400,  # 1 day
            samesite="lax",
        )

        return {"status": "success", "user": res, "access_token": access_token}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Registration failed")
        return JSONResponse(
            status_code=500, content={"detail": "Internal Server Error"}
        )


@app.post("/auth/login")
async def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and set Session Cookie"""
    user = await db_client.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="البريد الإلكتروني أو كلمة المرور غير صحيحة",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user["email"]})

    # Store Session in DB
    expires_at = (datetime.now() + timedelta(days=1)).isoformat()
    await db_client.create_session(user["id"], access_token, expires_at)

    # Set Secure Cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
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
    return current_user


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
    # Security Check for Web
    if payload.platform == "web":
        if not current_user:
            raise HTTPException(status_code=401, detail="Unauthorized Web Access")
        # Enforce real user_id
        payload.user_id = str(current_user["id"])

    logger.info(f"Received from {payload.user_id}: {payload.message}")

    user_id = payload.user_id
    message = payload.message.strip()

    # 1. SAVE USER MESSAGE 🧠
    # Only if it's a real integer ID (Web User)
    if payload.platform == "web":
        await db_client.save_message(int(user_id), "user", message)

    # 2. ROUTE MESSAGE 🚀
    response_text = ""

    # Check for direct tools first
    if message.startswith("/"):
        parts = message.split(" ", 1)
        command = parts[0]
        arg = parts[1] if len(parts) > 1 else ""

        tool_class = ToolRegistry.get_tool(command)
        if tool_class:
            logger.info(f"Executing tool: {command}")
            tool_instance = tool_class()
            try:
                result = await tool_instance.execute(arg, user_id)
                response_text = result.get("output", "")
                # Metadata could be useful later
            except Exception as e:
                response_text = f"❌ حدث خطأ أثناء تنفيذ الأداة: {str(e)}"
        else:
            response_text = f"⚠️ الأمر غير معروف: {command}"

    else:
        # 3. INTELLIGENT CHAT (LLM) 🤖
        # Retrieve Context
        context_str = ""
        if payload.platform == "web":
            history = await db_client.get_recent_messages(int(user_id), limit=5)
            # Format for LLM
            context_str = "\n".join(
                [f"{msg['role']}: {msg['content']}" for msg in history]
            )

        # Determine System Prompt
        system_persona = """
        أنت نوفا (Nova)، مساعد ذكي متطور من تطوير RobovAI Solutions.
        - تتحدث باللهجة المصرية الودودة أو العربية الفصحى المبسطة.
        - أنت محترف، ذكي، وتتمتع بحس فكاهي خفيف.
        - هدفك مساعدة المستخدم في مهامه.
        - إذا لم تفهم، اطلب التوضيح بأدب.
        """

        # Generate Response
        from backend.core.llm import llm_client

        prompt = f"Context:\n{context_str}\n\nUser: {message}"
        response_text = await llm_client.generate(prompt, system_prompt=system_persona)

    # 4. SAVE ASSISTANT RESPONSE 🧠
    if payload.platform == "web":
        await db_client.save_message(int(user_id), "assistant", response_text)

    return {"status": "success", "response": response_text}


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
async def upload_file(file: UploadFile = File(...)):
    """
    Generic file upload for multimodal interactions
    """
    try:
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
    file: UploadFile = File(...), user_id: str = Form("anonymous")
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


# Mount Public Assets & Uploads
app.mount("/public", StaticFiles(directory="public"), name="public")
app.mount("/static", StaticFiles(directory="public"), name="static")
# Mount uploads directory
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


@app.post("/telegram_webhook")
async def telegram_webhook(request: Request):
    """
    Telegram Bot Webhook
    Setup: https://api.telegram.org/bot<TOKEN>/setWebhook?url=YOUR_URL/telegram_webhook
    """
    try:
        from backend.adapters.platforms import TelegramAdapter, OutgoingMessage

        payload = await request.json()
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")

        if not bot_token:
            logger.error("TELEGRAM_BOT_TOKEN not set")
            return {"ok": True}

        adapter = TelegramAdapter(bot_token)
        message = await adapter.parse_webhook(payload)

        if not message:
            return {"ok": True}

        # Send typing indicator
        await adapter.send_typing(message.chat_id)

        # Route message
        from backend.core.smart_router import SmartToolRouter

        routing_result = await SmartToolRouter.route_message(
            message.text, message.user_id, platform="telegram"
        )

        # Get response
        if routing_result["type"] == "tool":
            response = routing_result["result"].get("output", "تم التنفيذ ✅")
        else:
            from backend.core.llm import llm_client

            response = await llm_client.generate(
                message.text,
                provider="groq",
                system_prompt="أنت RobovAI Nova Agent - مساعد ذكي مصري ودود. رد بالمصري العامي.",
            )

        # Send response
        await adapter.send_message(
            OutgoingMessage(
                text=response[:4000],  # Telegram limit
                chat_id=message.chat_id,
                reply_to=message.message_id,
            )
        )

        return {"ok": True}

    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        return {"ok": True}


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
                provider="groq",
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
                provider="groq",
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
async def get_user_stats(user_id: str):
    """Get user usage statistics"""
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
# 💳 LEMONSQUEEZY PAYMENTS
# ═══════════════════════════════════════════════════════════════════════════

from backend.lemonsqueezy import LemonSqueezyPayment, PRICING_TIERS


@app.post("/payments/checkout")
async def create_checkout(
    tier: str = "pro", current_user: dict = Depends(get_current_user)
):
    """Create LemonSqueezy checkout URL"""
    if tier not in ["pro", "enterprise"]:
        raise HTTPException(status_code=400, detail="Invalid tier")

    checkout_url = await LemonSqueezyPayment.create_checkout(
        user_id=str(current_user.get("id")),
        user_email=current_user.get("email"),
        tier=tier,
    )

    if not checkout_url:
        raise HTTPException(status_code=503, detail="Payment service unavailable")

    return {"checkout_url": checkout_url}


@app.post("/payments/webhook")
async def lemonsqueezy_webhook(request: Request):
    """Handle LemonSqueezy webhook events"""
    signature = request.headers.get("X-Signature", "")
    payload = await request.body()

    # Verify signature
    if not LemonSqueezyPayment.verify_webhook(payload, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    data = await request.json()
    event_name = data.get("meta", {}).get("event_name", "")

    await LemonSqueezyPayment.process_webhook(event_name, data, db_client)

    return {"status": "ok"}


@app.get("/payments/pricing")
async def get_pricing():
    """Get pricing tiers"""
    return PRICING_TIERS


@app.get("/payments/subscription")
async def get_subscription(current_user: dict = Depends(get_current_user)):
    """Get user's current subscription"""
    from backend.payments import PaymentSystem

    subscription = await PaymentSystem.check_subscription(
        str(current_user.get("id")), db_client
    )
    return subscription


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "tools_count": len(ToolRegistry.list_tools()),
        "platforms": ["web", "telegram", "whatsapp", "messenger", "discord"],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

    uvicorn.run(app, host="0.0.0.0", port=8000)
