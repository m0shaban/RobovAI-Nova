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


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads (presentations, files, etc.)
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


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


@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    """
    Telegram Bot Webhook
    Setup: https://api.telegram.org/bot<TOKEN>/setWebhook?url=YOUR_URL/telegram-webhook
    """
    try:
        logger.info("📨 Telegram webhook received")

        from backend.adapters.platforms import TelegramAdapter, OutgoingMessage

        payload = await request.json()
        logger.info(f"Telegram payload: {payload}")

        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")

        if not bot_token:
            logger.error("❌ TELEGRAM_BOT_TOKEN not set")
            return {"ok": True}

        adapter = TelegramAdapter(bot_token)
        message = await adapter.parse_webhook(payload)

        if not message:
            logger.info("No message to process (might be a non-message update)")
            return {"ok": True}

        logger.info(f"📩 Received message from user {message.user_id}: {message.text}")

        # Send typing indicator
        await adapter.send_typing(message.chat_id)

        # Route message
        from backend.core.smart_router import SmartToolRouter

        try:
            routing_result = await SmartToolRouter.route_message(
                message.text, message.user_id, platform="telegram"
            )

            # Get response
            if routing_result["type"] == "tool":
                response = routing_result["result"].get("output", "تم التنفيذ ✅")
                logger.info(f"Tool response generated for user {message.user_id}")
            else:
                from backend.core.llm import llm_client

                response = await llm_client.generate(
                    message.text,
                    provider="auto",
                    system_prompt="أنت RobovAI Nova Agent - مساعد ذكي مصري ودود. رد بالمصري العامي.",
                )
                logger.info(f"LLM response generated for user {message.user_id}")

            # Send response
            await adapter.send_message(
                OutgoingMessage(
                    text=response[:4000],  # Telegram limit
                    chat_id=message.chat_id,
                    reply_to=message.message_id,
                )
            )

            logger.info(f"✅ Successfully sent response to user {message.user_id}")

        except Exception as routing_error:
            logger.error(f"❌ Routing/LLM error: {routing_error}", exc_info=True)
            # Send error message to user
            try:
                await adapter.send_message(
                    OutgoingMessage(
                        text="⚠️ **حدث خطأ تقني.**\nعذراً، لم أتمكن من معالجة طلبك. يرجى المحاولة مرة أخرى.",
                        chat_id=message.chat_id,
                        reply_to=message.message_id,
                    )
                )
            except:
                pass

        return {"ok": True}

    except Exception as e:
        logger.error(f"❌ Telegram webhook critical error: {e}", exc_info=True)
        # Try to notify user if possible
        try:
            payload = await request.json()
            msg = payload.get("message") or payload.get("edited_message")
            if msg:
                chat_id = msg.get("chat", {}).get("id")
                message_id = msg.get("message_id")
                if chat_id:
                    from backend.adapters.platforms import (
                        TelegramAdapter,
                        OutgoingMessage,
                    )

                    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
                    if bot_token:
                        adapter = TelegramAdapter(bot_token)
                        await adapter.send_message(
                            OutgoingMessage(
                                text="⚠️ **حدث خطأ تقني.**\nعذراً، لم أتمكن من معالجة طلبك.",
                                chat_id=str(chat_id),
                                reply_to=str(message_id) if message_id else None,
                            )
                        )
        except Exception as notify_error:
            logger.error(f"Failed to notify user of error: {notify_error}")

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
    message: str, user_id: str = "web_user", platform: str = "web"
):
    """
    🔄 Stream agent execution step by step (GET version for EventSource)

    Returns Server-Sent Events for real-time updates.
    """
    return await _stream_agent(message, user_id, platform)


async def _stream_agent(message: str, user_id: str, platform: str):
    """Internal streaming function used by both GET and POST endpoints"""
    from fastapi.responses import StreamingResponse
    import json

    async def event_generator():
        try:
            from backend.agent.graph import NovaAgent
            import asyncio

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
async def list_conversations(user_id: str = "default"):
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
async def get_conversation(conv_id: str, user_id: str = "default"):
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
async def create_conversation(user_id: str = "default", title: str = "محادثة جديدة"):
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
async def add_message(conv_id: str, role: str, content: str, user_id: str = "default"):
    """إضافة رسالة"""
    try:
        from backend.history.manager import get_conversation_manager

        manager = get_conversation_manager()
        msg = manager.add_message(user_id, conv_id, role, content)
        return {"status": "success", "message_id": msg.id}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/history/search")
async def search_conversations(user_id: str, query: str, limit: int = 10):
    """بحث في المحادثات"""
    try:
        from backend.history.manager import get_conversation_manager

        manager = get_conversation_manager()
        results = manager.search_conversations(user_id, query, limit)
        return {"status": "success", "results": results}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.delete("/history/conversation/{conv_id}")
async def delete_conversation(conv_id: str, user_id: str = "default"):
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
    conv_id: str, user_id: str = "default", format: str = "json"
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
async def get_admin_stats():
    """إحصائيات لوحة التحكم"""
    try:
        tools = ToolRegistry.list_tools()

        # إحصائيات الأدوات
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
                "system": {
                    "uptime": "running",
                    "version": "2.0.0",
                    "agent": "Nova Multi-Agent",
                },
            },
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/admin/tools")
async def get_tools_detailed():
    """قائمة الأدوات مع التفاصيل"""
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
async def get_user_memory(user_id: str):
    """الحصول على ذاكرة المستخدم"""
    try:
        from backend.agent.memory import get_memory_manager

        manager = get_memory_manager()
        context = manager.get_context(user_id, f"session_{user_id}")
        return {"status": "success", "memory": context}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/admin/logs")
async def get_system_logs(limit: int = 50):
    """الحصول على آخر السجلات"""
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
