"""
🌐 RobovAI Nova - Multi-Platform Adapters
═══════════════════════════════════════════════════════════════

Supported Platforms:
✅ Telegram Bot
✅ WhatsApp (via Twilio/Meta API)
✅ Facebook Messenger
✅ Web Widget
✅ Discord (bonus)
✅ Slack (bonus)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import hashlib
import json
import httpx
import logging
from datetime import datetime

logger = logging.getLogger("robovai.adapters")


# ═══════════════════════════════════════════════════════════════════════════
# 📦 BASE ADAPTER
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class IncomingMessage:
    """Standardized incoming message format"""
    platform: str
    user_id: str
    chat_id: str
    text: str
    message_id: str
    timestamp: datetime
    attachments: List[Dict[str, Any]] = None
    reply_to: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        self.attachments = self.attachments or []
        self.metadata = self.metadata or {}


@dataclass 
class OutgoingMessage:
    """Standardized outgoing message format"""
    text: str
    chat_id: str
    parse_mode: str = "markdown"
    attachments: List[Dict[str, Any]] = None
    reply_to: Optional[str] = None
    buttons: List[Dict[str, str]] = None
    
    def __post_init__(self):
        self.attachments = self.attachments or []
        self.buttons = self.buttons or []


class BasePlatformAdapter(ABC):
    """Base class for all platform adapters"""
    
    platform_name: str = "base"
    
    @abstractmethod
    async def parse_webhook(self, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        """Parse incoming webhook payload to standard format"""
        pass
    
    @abstractmethod
    async def send_message(self, message: OutgoingMessage) -> bool:
        """Send message to the platform"""
        pass
    
    @abstractmethod
    async def send_typing(self, chat_id: str) -> bool:
        """Send typing indicator"""
        pass
    
    def sanitize_markdown(self, text: str) -> str:
        """Convert markdown to platform-specific format"""
        return text


# ═══════════════════════════════════════════════════════════════════════════
# 📱 TELEGRAM ADAPTER
# ═══════════════════════════════════════════════════════════════════════════

class TelegramAdapter(BasePlatformAdapter):
    """
    Telegram Bot Adapter
    
    Setup:
    1. Create bot via @BotFather
    2. Get token
    3. Set webhook: https://api.telegram.org/bot<TOKEN>/setWebhook?url=YOUR_URL/telegram_webhook
    """
    
    platform_name = "telegram"
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.api_base = f"https://api.telegram.org/bot{bot_token}"
    
    async def parse_webhook(self, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        """Parse Telegram webhook payload"""
        try:
            # Handle message updates
            message = payload.get("message") or payload.get("edited_message")
            if not message:
                return None
            
            user = message.get("from", {})
            chat = message.get("chat", {})
            
            # Handle attachments
            attachments = []
            
            if "photo" in message:
                # Get highest resolution photo
                photo = message["photo"][-1]
                attachments.append({
                    "type": "photo",
                    "file_id": photo["file_id"],
                    "width": photo.get("width"),
                    "height": photo.get("height")
                })
            
            if "voice" in message:
                attachments.append({
                    "type": "voice",
                    "file_id": message["voice"]["file_id"],
                    "duration": message["voice"].get("duration")
                })
            
            if "document" in message:
                doc = message["document"]
                attachments.append({
                    "type": "document",
                    "file_id": doc["file_id"],
                    "file_name": doc.get("file_name"),
                    "mime_type": doc.get("mime_type")
                })
            
            return IncomingMessage(
                platform="telegram",
                user_id=str(user.get("id")),
                chat_id=str(chat.get("id")),
                text=message.get("text") or message.get("caption") or "",
                message_id=str(message.get("message_id")),
                timestamp=datetime.fromtimestamp(message.get("date", 0)),
                attachments=attachments,
                reply_to=str(message.get("reply_to_message", {}).get("message_id")) if message.get("reply_to_message") else None,
                metadata={
                    "username": user.get("username"),
                    "first_name": user.get("first_name"),
                    "last_name": user.get("last_name"),
                    "chat_type": chat.get("type")
                }
            )
        except Exception as e:
            logger.error(f"Telegram parse error: {e}")
            return None
    
    async def send_message(self, message: OutgoingMessage) -> bool:
        """Send message via Telegram with automatic fallback"""
        try:
            base_payload = {
                "chat_id": message.chat_id,
                "text": message.text,
            }
            
            if message.reply_to:
                base_payload["reply_to_message_id"] = message.reply_to
            
            # Add inline keyboard if buttons provided
            if message.buttons:
                keyboard = [[{"text": btn["text"], "callback_data": btn.get("data", btn["text"])}] 
                           for btn in message.buttons]
                base_payload["reply_markup"] = json.dumps({"inline_keyboard": keyboard})
            
            async with httpx.AsyncClient() as client:
                # Try 1: With HTML formatting
                try:
                    payload = {**base_payload, "parse_mode": "HTML"}
                    resp = await client.post(
                        f"{self.api_base}/sendMessage",
                        json=payload,
                        timeout=30.0
                    )
                    if resp.status_code == 200:
                        return True
                    logger.warning(f"HTML send failed: {resp.status_code} - {resp.text}")
                except Exception as e:
                    logger.warning(f"HTML send exception: {e}")
                
                # Try 2: Plain text (no formatting)
                try:
                    payload = {**base_payload}  # No parse_mode
                    resp = await client.post(
                        f"{self.api_base}/sendMessage",
                        json=payload,
                        timeout=30.0
                    )
                    if resp.status_code == 200:
                        logger.info("Sent as plain text (fallback)")
                        return True
                    logger.error(f"Plain text send failed: {resp.status_code} - {resp.text}")
                except Exception as e:
                    logger.error(f"Plain text send exception: {e}")
                
                return False
                
        except Exception as e:
            logger.error(f"Telegram send error: {e}")
            return False
    
    async def send_typing(self, chat_id: str) -> bool:
        """Send typing indicator"""
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.api_base}/sendChatAction",
                    json={"chat_id": chat_id, "action": "typing"}
                )
            return True
        except:
            return False
    
    async def get_file_url(self, file_id: str) -> Optional[str]:
        """Get download URL for file"""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.api_base}/getFile?file_id={file_id}")
                data = resp.json()
                if data.get("ok"):
                    file_path = data["result"]["file_path"]
                    return f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
        except:
            pass
        return None
    
    def sanitize_markdown(self, text: str) -> str:
        """Escape special characters for Telegram MarkdownV2"""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text


# ═══════════════════════════════════════════════════════════════════════════
# 📱 WHATSAPP ADAPTER (via Meta/Twilio)
# ═══════════════════════════════════════════════════════════════════════════

class WhatsAppAdapter(BasePlatformAdapter):
    """
    WhatsApp Business API Adapter
    
    Supports:
    - Meta Cloud API (recommended)
    - Twilio WhatsApp
    """
    
    platform_name = "whatsapp"
    
    def __init__(self, access_token: str, phone_number_id: str, verify_token: str = "robovai_verify"):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.verify_token = verify_token
        self.api_base = f"https://graph.facebook.com/v18.0/{phone_number_id}"
    
    async def parse_webhook(self, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        """Parse WhatsApp webhook payload"""
        try:
            entry = payload.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            
            messages = value.get("messages", [])
            if not messages:
                return None
            
            message = messages[0]
            contact = value.get("contacts", [{}])[0]
            
            # Extract text
            text = ""
            attachments = []
            
            msg_type = message.get("type")
            
            if msg_type == "text":
                text = message.get("text", {}).get("body", "")
            elif msg_type == "image":
                attachments.append({
                    "type": "image",
                    "media_id": message.get("image", {}).get("id")
                })
                text = message.get("image", {}).get("caption", "")
            elif msg_type == "audio":
                attachments.append({
                    "type": "audio",
                    "media_id": message.get("audio", {}).get("id")
                })
            elif msg_type == "document":
                doc = message.get("document", {})
                attachments.append({
                    "type": "document",
                    "media_id": doc.get("id"),
                    "filename": doc.get("filename")
                })
            
            return IncomingMessage(
                platform="whatsapp",
                user_id=message.get("from"),
                chat_id=message.get("from"),
                text=text,
                message_id=message.get("id"),
                timestamp=datetime.fromtimestamp(int(message.get("timestamp", 0))),
                attachments=attachments,
                metadata={
                    "name": contact.get("profile", {}).get("name"),
                    "wa_id": contact.get("wa_id")
                }
            )
        except Exception as e:
            logger.error(f"WhatsApp parse error: {e}")
            return None
    
    async def send_message(self, message: OutgoingMessage) -> bool:
        """Send message via WhatsApp"""
        try:
            payload = {
                "messaging_product": "whatsapp",
                "to": message.chat_id,
                "type": "text",
                "text": {"body": message.text}
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.api_base}/messages",
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                return resp.status_code == 200
                
        except Exception as e:
            logger.error(f"WhatsApp send error: {e}")
            return False
    
    async def send_typing(self, chat_id: str) -> bool:
        """WhatsApp doesn't have a typing indicator API"""
        return True
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Verify webhook for WhatsApp"""
        if mode == "subscribe" and token == self.verify_token:
            return challenge
        return None


# ═══════════════════════════════════════════════════════════════════════════
# 📱 MESSENGER ADAPTER (Facebook)
# ═══════════════════════════════════════════════════════════════════════════

class MessengerAdapter(BasePlatformAdapter):
    """
    Facebook Messenger Adapter
    """
    
    platform_name = "messenger"
    
    def __init__(self, page_access_token: str, verify_token: str = "robovai_verify"):
        self.page_access_token = page_access_token
        self.verify_token = verify_token
        self.api_base = "https://graph.facebook.com/v18.0/me"
    
    async def parse_webhook(self, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        """Parse Messenger webhook payload"""
        try:
            entry = payload.get("entry", [{}])[0]
            messaging = entry.get("messaging", [{}])[0]
            
            sender = messaging.get("sender", {})
            message = messaging.get("message", {})
            
            if not message:
                return None
            
            attachments = []
            for att in message.get("attachments", []):
                attachments.append({
                    "type": att.get("type"),
                    "url": att.get("payload", {}).get("url")
                })
            
            return IncomingMessage(
                platform="messenger",
                user_id=sender.get("id"),
                chat_id=sender.get("id"),
                text=message.get("text", ""),
                message_id=message.get("mid"),
                timestamp=datetime.fromtimestamp(entry.get("time", 0) / 1000),
                attachments=attachments
            )
        except Exception as e:
            logger.error(f"Messenger parse error: {e}")
            return None
    
    async def send_message(self, message: OutgoingMessage) -> bool:
        """Send message via Messenger"""
        try:
            payload = {
                "recipient": {"id": message.chat_id},
                "message": {"text": message.text}
            }
            
            # Add quick replies (buttons)
            if message.buttons:
                payload["message"]["quick_replies"] = [
                    {"content_type": "text", "title": btn["text"], "payload": btn.get("data", btn["text"])}
                    for btn in message.buttons[:13]  # Max 13 quick replies
                ]
            
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.api_base}/messages",
                    params={"access_token": self.page_access_token},
                    json=payload,
                    timeout=30.0
                )
                return resp.status_code == 200
                
        except Exception as e:
            logger.error(f"Messenger send error: {e}")
            return False
    
    async def send_typing(self, chat_id: str) -> bool:
        """Send typing indicator"""
        try:
            payload = {
                "recipient": {"id": chat_id},
                "sender_action": "typing_on"
            }
            
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.api_base}/messages",
                    params={"access_token": self.page_access_token},
                    json=payload
                )
            return True
        except:
            return False


# ═══════════════════════════════════════════════════════════════════════════
# 🌐 WEB WIDGET ADAPTER
# ═══════════════════════════════════════════════════════════════════════════

class WebWidgetAdapter(BasePlatformAdapter):
    """
    Web Chat Widget Adapter
    For embedding in websites
    """
    
    platform_name = "web"
    
    def __init__(self, api_endpoint: str = "/api/chat"):
        self.api_endpoint = api_endpoint
    
    async def parse_webhook(self, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        """Parse web widget payload"""
        try:
            return IncomingMessage(
                platform="web",
                user_id=payload.get("user_id", "anonymous"),
                chat_id=payload.get("session_id", payload.get("user_id", "anonymous")),
                text=payload.get("message", ""),
                message_id=payload.get("message_id", str(datetime.now().timestamp())),
                timestamp=datetime.now(),
                attachments=payload.get("attachments", []),
                metadata=payload.get("metadata", {})
            )
        except Exception as e:
            logger.error(f"Web widget parse error: {e}")
            return None
    
    async def send_message(self, message: OutgoingMessage) -> bool:
        """Web widget messages are returned directly, not sent"""
        return True
    
    async def send_typing(self, chat_id: str) -> bool:
        """Typing handled by frontend"""
        return True
    
    def generate_embed_code(self, base_url: str) -> str:
        """Generate JavaScript embed code for websites"""
        return f'''
<!-- RobovAI Nova Chat Widget -->
<script>
(function() {{
    var script = document.createElement('script');
    script.src = '{base_url}/static/widget.js';
    script.async = true;
    script.onload = function() {{
        RobovAI.init({{
            apiEndpoint: '{base_url}/webhook',
            theme: 'dark',
            position: 'bottom-right',
            greeting: 'أهلاً! أنا RobovAI Nova 🤖'
        }});
    }};
    document.head.appendChild(script);
}})();
</script>
'''


# ═══════════════════════════════════════════════════════════════════════════
# 🎮 DISCORD ADAPTER (Bonus)
# ═══════════════════════════════════════════════════════════════════════════

class DiscordAdapter(BasePlatformAdapter):
    """Discord Bot Adapter"""
    
    platform_name = "discord"
    
    def __init__(self, bot_token: str, application_id: str):
        self.bot_token = bot_token
        self.application_id = application_id
        self.api_base = "https://discord.com/api/v10"
    
    async def parse_webhook(self, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        """Parse Discord interaction/message"""
        try:
            # Handle slash commands
            if payload.get("type") == 2:  # APPLICATION_COMMAND
                data = payload.get("data", {})
                user = payload.get("member", {}).get("user") or payload.get("user", {})
                
                options = {opt["name"]: opt.get("value") for opt in data.get("options", [])}
                
                return IncomingMessage(
                    platform="discord",
                    user_id=user.get("id"),
                    chat_id=payload.get("channel_id"),
                    text=f"/{data.get('name')} {' '.join(str(v) for v in options.values())}".strip(),
                    message_id=payload.get("id"),
                    timestamp=datetime.now(),
                    metadata={"guild_id": payload.get("guild_id"), "options": options}
                )
            
            # Handle regular messages
            if "content" in payload:
                author = payload.get("author", {})
                return IncomingMessage(
                    platform="discord",
                    user_id=author.get("id"),
                    chat_id=payload.get("channel_id"),
                    text=payload.get("content", ""),
                    message_id=payload.get("id"),
                    timestamp=datetime.fromisoformat(payload.get("timestamp", datetime.now().isoformat()).replace('Z', '+00:00'))
                )
                
        except Exception as e:
            logger.error(f"Discord parse error: {e}")
        return None
    
    async def send_message(self, message: OutgoingMessage) -> bool:
        """Send message to Discord channel"""
        try:
            headers = {
                "Authorization": f"Bot {self.bot_token}",
                "Content-Type": "application/json"
            }
            
            payload = {"content": message.text}
            
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.api_base}/channels/{message.chat_id}/messages",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                return resp.status_code == 200
                
        except Exception as e:
            logger.error(f"Discord send error: {e}")
            return False
    
    async def send_typing(self, chat_id: str) -> bool:
        """Trigger typing indicator"""
        try:
            headers = {"Authorization": f"Bot {self.bot_token}"}
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.api_base}/channels/{chat_id}/typing",
                    headers=headers
                )
            return True
        except:
            return False


# ═══════════════════════════════════════════════════════════════════════════
# 🏭 ADAPTER FACTORY
# ═══════════════════════════════════════════════════════════════════════════

class AdapterFactory:
    """Factory for creating platform adapters"""
    
    _adapters = {
        "telegram": TelegramAdapter,
        "whatsapp": WhatsAppAdapter,
        "messenger": MessengerAdapter,
        "web": WebWidgetAdapter,
        "discord": DiscordAdapter,
    }
    
    @classmethod
    def create(cls, platform: str, **kwargs) -> BasePlatformAdapter:
        """Create adapter for specified platform"""
        adapter_class = cls._adapters.get(platform.lower())
        if not adapter_class:
            raise ValueError(f"Unknown platform: {platform}")
        return adapter_class(**kwargs)
    
    @classmethod
    def list_platforms(cls) -> List[str]:
        """List available platforms"""
        return list(cls._adapters.keys())
