"""
📜 Nova Agent - Conversation History Manager
============================================

نظام إدارة المحادثات:
- حفظ واسترجاع المحادثات
- بحث في التاريخ
- تصدير بصيغ متعددة
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

# مجلد تخزين المحادثات
HISTORY_DIR = Path("data/conversations")
HISTORY_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Message:
    """رسالة واحدة"""
    id: str
    role: str  # user, assistant, system
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Conversation:
    """محادثة كاملة"""
    id: str
    user_id: str
    title: str
    messages: List[Message] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    is_archived: bool = False
    is_favorite: bool = False


class ConversationManager:
    """
    📜 مدير المحادثات
    
    يدير:
    - إنشاء محادثات جديدة
    - إضافة رسائل
    - البحث في التاريخ
    - التصدير والحذف
    """
    
    def __init__(self):
        self._cache: Dict[str, Conversation] = {}
        logger.info("📜 ConversationManager initialized")
    
    def _get_user_dir(self, user_id: str) -> Path:
        """مجلد المستخدم"""
        safe_id = hashlib.md5(user_id.encode()).hexdigest()[:16]
        user_dir = HISTORY_DIR / safe_id
        user_dir.mkdir(exist_ok=True)
        return user_dir
    
    def _get_conversation_path(self, user_id: str, conv_id: str) -> Path:
        """مسار ملف المحادثة"""
        return self._get_user_dir(user_id) / f"{conv_id}.json"
    
    def create_conversation(self, user_id: str, title: str = "محادثة جديدة") -> Conversation:
        """إنشاء محادثة جديدة"""
        conv_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        conv = Conversation(
            id=conv_id,
            user_id=user_id,
            title=title
        )
        
        self.save_conversation(conv)
        self._cache[conv_id] = conv
        
        logger.info(f"📝 Created conversation {conv_id}")
        return conv
    
    def save_conversation(self, conv: Conversation):
        """حفظ محادثة"""
        conv.updated_at = datetime.now().isoformat()
        path = self._get_conversation_path(conv.user_id, conv.id)
        
        # تحويل Messages لـ dict
        data = {
            **asdict(conv),
            "messages": [asdict(m) for m in conv.messages]
        }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_conversation(self, user_id: str, conv_id: str) -> Optional[Conversation]:
        """الحصول على محادثة"""
        if conv_id in self._cache:
            return self._cache[conv_id]
        
        path = self._get_conversation_path(user_id, conv_id)
        if not path.exists():
            return None
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # تحويل dict لـ Messages
        messages = [Message(**m) for m in data.pop("messages", [])]
        conv = Conversation(**data, messages=messages)
        
        self._cache[conv_id] = conv
        return conv
    
    def add_message(self, user_id: str, conv_id: str, role: str, content: str, metadata: Dict = None) -> Message:
        """إضافة رسالة لمحادثة"""
        conv = self.get_conversation(user_id, conv_id)
        if not conv:
            conv = self.create_conversation(user_id)
        
        msg = Message(
            id=f"msg_{len(conv.messages)}",
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        conv.messages.append(msg)
        
        # تحديث العنوان من أول رسالة user
        if role == "user" and len(conv.messages) == 1:
            conv.title = content[:50] + ("..." if len(content) > 50 else "")
        
        self.save_conversation(conv)
        return msg
    
    def list_conversations(self, user_id: str, include_archived: bool = False) -> List[Dict]:
        """قائمة محادثات المستخدم"""
        user_dir = self._get_user_dir(user_id)
        conversations = []
        
        for path in user_dir.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                if not include_archived and data.get("is_archived"):
                    continue
                
                conversations.append({
                    "id": data["id"],
                    "title": data["title"],
                    "created_at": data["created_at"],
                    "updated_at": data["updated_at"],
                    "message_count": len(data.get("messages", [])),
                    "is_favorite": data.get("is_favorite", False),
                    "tags": data.get("tags", [])
                })
            except Exception as e:
                logger.warning(f"Error reading conversation {path}: {e}")
        
        # ترتيب حسب آخر تحديث
        conversations.sort(key=lambda c: c["updated_at"], reverse=True)
        return conversations
    
    def search_conversations(self, user_id: str, query: str, limit: int = 10) -> List[Dict]:
        """بحث في المحادثات"""
        user_dir = self._get_user_dir(user_id)
        results = []
        query_lower = query.lower()
        
        for path in user_dir.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # بحث في العنوان والرسائل
                found = False
                matched_messages = []
                
                if query_lower in data.get("title", "").lower():
                    found = True
                
                for msg in data.get("messages", []):
                    if query_lower in msg.get("content", "").lower():
                        found = True
                        matched_messages.append({
                            "role": msg["role"],
                            "content": msg["content"][:100],
                            "timestamp": msg["timestamp"]
                        })
                
                if found:
                    results.append({
                        "id": data["id"],
                        "title": data["title"],
                        "updated_at": data["updated_at"],
                        "matched_messages": matched_messages[:3]
                    })
            except Exception as e:
                logger.warning(f"Error searching {path}: {e}")
        
        return results[:limit]
    
    def delete_conversation(self, user_id: str, conv_id: str) -> bool:
        """حذف محادثة"""
        path = self._get_conversation_path(user_id, conv_id)
        if path.exists():
            os.remove(path)
            self._cache.pop(conv_id, None)
            logger.info(f"🗑️ Deleted conversation {conv_id}")
            return True
        return False
    
    def archive_conversation(self, user_id: str, conv_id: str) -> bool:
        """أرشفة محادثة"""
        conv = self.get_conversation(user_id, conv_id)
        if conv:
            conv.is_archived = True
            self.save_conversation(conv)
            return True
        return False
    
    def toggle_favorite(self, user_id: str, conv_id: str) -> bool:
        """تبديل المفضلة"""
        conv = self.get_conversation(user_id, conv_id)
        if conv:
            conv.is_favorite = not conv.is_favorite
            self.save_conversation(conv)
            return conv.is_favorite
        return False
    
    def export_conversation(self, user_id: str, conv_id: str, format: str = "json") -> Optional[str]:
        """تصدير محادثة"""
        conv = self.get_conversation(user_id, conv_id)
        if not conv:
            return None
        
        if format == "json":
            return json.dumps(asdict(conv), ensure_ascii=False, indent=2)
        
        elif format == "text":
            lines = [f"# {conv.title}", f"تاريخ: {conv.created_at}", ""]
            for msg in conv.messages:
                role_name = "المستخدم" if msg.role == "user" else "نوفا"
                lines.append(f"**{role_name}**: {msg.content}")
                lines.append("")
            return "\n".join(lines)
        
        elif format == "html":
            html = f"""<!DOCTYPE html>
<html dir="rtl">
<head><meta charset="UTF-8"><title>{conv.title}</title>
<style>
body {{ font-family: 'Cairo', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
.user {{ background: #e3f2fd; padding: 10px; border-radius: 10px; margin: 10px 0; }}
.assistant {{ background: #f5f5f5; padding: 10px; border-radius: 10px; margin: 10px 0; }}
</style></head>
<body>
<h1>{conv.title}</h1>
<p>تاريخ: {conv.created_at}</p>
"""
            for msg in conv.messages:
                role_class = msg.role
                role_name = "المستخدم" if msg.role == "user" else "نوفا"
                html += f'<div class="{role_class}"><strong>{role_name}:</strong> {msg.content}</div>\n'
            html += "</body></html>"
            return html
        
        return None
    
    def get_stats(self, user_id: str) -> Dict[str, Any]:
        """إحصائيات المستخدم"""
        conversations = self.list_conversations(user_id, include_archived=True)
        
        total_messages = 0
        total_user_messages = 0
        
        for conv in conversations:
            try:
                full_conv = self.get_conversation(user_id, conv["id"])
                if full_conv:
                    total_messages += len(full_conv.messages)
                    total_user_messages += sum(1 for m in full_conv.messages if m.role == "user")
            except:
                pass
        
        return {
            "total_conversations": len(conversations),
            "total_messages": total_messages,
            "total_user_messages": total_user_messages,
            "favorites_count": sum(1 for c in conversations if c.get("is_favorite")),
            "archived_count": sum(1 for c in conversations if c.get("is_archived"))
        }


# Singleton
_manager: Optional[ConversationManager] = None

def get_conversation_manager() -> ConversationManager:
    """الحصول على instance من ConversationManager"""
    global _manager
    if _manager is None:
        _manager = ConversationManager()
    return _manager
