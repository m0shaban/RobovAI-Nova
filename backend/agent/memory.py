"""
🧠 Nova Agent - Enhanced Memory System
=======================================

نظام ذاكرة متقدم يتضمن:
- Short-term Memory: سياق المحادثة الحالية
- Long-term Memory: تفضيلات المستخدم والتاريخ
- Semantic Memory: embeddings للبحث السريع
"""

import json
import os
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)

# مجلد تخزين الذاكرة
MEMORY_DIR = Path("data/memory")
MEMORY_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class MemoryEntry:
    """إدخال في الذاكرة"""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    importance: float = 0.5  # 0-1 أهمية الذكرى
    access_count: int = 0
    last_accessed: Optional[str] = None
    embedding: Optional[List[float]] = None


@dataclass
class ConversationContext:
    """سياق المحادثة الحالية"""
    messages: List[Dict[str, str]] = field(default_factory=list)
    current_topic: Optional[str] = None
    user_intent: Optional[str] = None
    active_tools: List[str] = field(default_factory=list)
    pending_tasks: List[str] = field(default_factory=list)
    

@dataclass
class UserProfile:
    """ملف المستخدم"""
    user_id: str
    name: Optional[str] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    interests: List[str] = field(default_factory=list)
    language: str = "ar"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())
    total_interactions: int = 0
    favorite_tools: List[str] = field(default_factory=list)


class ShortTermMemory:
    """
    🔄 الذاكرة قصيرة المدى
    
    تحتفظ بسياق المحادثة الحالية:
    - آخر N رسائل
    - الموضوع الحالي
    - الأدوات المستخدمة
    """
    
    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        self.contexts: Dict[str, ConversationContext] = {}
    
    def get_context(self, session_id: str) -> ConversationContext:
        """الحصول على سياق جلسة معينة"""
        if session_id not in self.contexts:
            self.contexts[session_id] = ConversationContext()
        return self.contexts[session_id]
    
    def add_message(self, session_id: str, role: str, content: str):
        """إضافة رسالة للسياق"""
        context = self.get_context(session_id)
        context.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # الاحتفاظ بآخر N رسائل فقط
        if len(context.messages) > self.max_messages:
            context.messages = context.messages[-self.max_messages:]
    
    def get_recent_messages(self, session_id: str, count: int = 10) -> List[Dict]:
        """الحصول على آخر N رسائل"""
        context = self.get_context(session_id)
        return context.messages[-count:]
    
    def set_topic(self, session_id: str, topic: str):
        """تعيين الموضوع الحالي"""
        context = self.get_context(session_id)
        context.current_topic = topic
    
    def add_active_tool(self, session_id: str, tool_name: str):
        """إضافة أداة نشطة"""
        context = self.get_context(session_id)
        if tool_name not in context.active_tools:
            context.active_tools.append(tool_name)
    
    def clear(self, session_id: str):
        """مسح سياق جلسة"""
        if session_id in self.contexts:
            del self.contexts[session_id]
    
    def get_summary(self, session_id: str) -> str:
        """الحصول على ملخص السياق"""
        context = self.get_context(session_id)
        
        summary_parts = []
        if context.current_topic:
            summary_parts.append(f"الموضوع: {context.current_topic}")
        if context.messages:
            summary_parts.append(f"عدد الرسائل: {len(context.messages)}")
        if context.active_tools:
            summary_parts.append(f"الأدوات: {', '.join(context.active_tools)}")
        
        return " | ".join(summary_parts) if summary_parts else "سياق فارغ"


class LongTermMemory:
    """
    💾 الذاكرة طويلة المدى
    
    تحتفظ بـ:
    - ملف المستخدم
    - التفضيلات
    - المحادثات السابقة المهمة
    """
    
    def __init__(self):
        self.profiles_dir = MEMORY_DIR / "profiles"
        self.memories_dir = MEMORY_DIR / "memories"
        self.profiles_dir.mkdir(exist_ok=True)
        self.memories_dir.mkdir(exist_ok=True)
        self._cache: Dict[str, UserProfile] = {}
    
    def _get_profile_path(self, user_id: str) -> Path:
        """مسار ملف المستخدم"""
        safe_id = hashlib.md5(user_id.encode()).hexdigest()[:16]
        return self.profiles_dir / f"{safe_id}.json"
    
    def get_profile(self, user_id: str) -> UserProfile:
        """الحصول على ملف المستخدم"""
        if user_id in self._cache:
            return self._cache[user_id]
        
        path = self._get_profile_path(user_id)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                profile = UserProfile(**data)
        else:
            profile = UserProfile(user_id=user_id)
            self.save_profile(profile)
        
        self._cache[user_id] = profile
        return profile
    
    def save_profile(self, profile: UserProfile):
        """حفظ ملف المستخدم"""
        profile.last_active = datetime.now().isoformat()
        path = self._get_profile_path(profile.user_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(profile), f, ensure_ascii=False, indent=2)
        self._cache[profile.user_id] = profile
    
    def update_preference(self, user_id: str, key: str, value: Any):
        """تحديث تفضيل معين"""
        profile = self.get_profile(user_id)
        profile.preferences[key] = value
        self.save_profile(profile)
    
    def add_interest(self, user_id: str, interest: str):
        """إضافة اهتمام"""
        profile = self.get_profile(user_id)
        if interest not in profile.interests:
            profile.interests.append(interest)
            self.save_profile(profile)
    
    def add_favorite_tool(self, user_id: str, tool_name: str):
        """إضافة أداة مفضلة"""
        profile = self.get_profile(user_id)
        if tool_name not in profile.favorite_tools:
            profile.favorite_tools.append(tool_name)
            # الاحتفاظ بأعلى 10 أدوات فقط
            profile.favorite_tools = profile.favorite_tools[-10:]
            self.save_profile(profile)
    
    def increment_interactions(self, user_id: str):
        """زيادة عداد التفاعلات"""
        profile = self.get_profile(user_id)
        profile.total_interactions += 1
        self.save_profile(profile)
    
    # =============== إدارة الذكريات ===============
    
    def _get_memories_path(self, user_id: str) -> Path:
        """مسار ملف ذكريات المستخدم"""
        safe_id = hashlib.md5(user_id.encode()).hexdigest()[:16]
        return self.memories_dir / f"{safe_id}.json"
    
    def save_memory(self, user_id: str, content: str, importance: float = 0.5, metadata: Dict = None):
        """حفظ ذكرى جديدة"""
        path = self._get_memories_path(user_id)
        
        # تحميل الذكريات الموجودة
        memories = []
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                memories = json.load(f)
        
        # إنشاء ذكرى جديدة
        memory = MemoryEntry(
            id=hashlib.md5(f"{content}{datetime.now()}".encode()).hexdigest()[:12],
            content=content,
            metadata=metadata or {},
            importance=importance
        )
        memories.append(asdict(memory))
        
        # الاحتفاظ بآخر 100 ذكرى فقط
        if len(memories) > 100:
            # حذف الأقل أهمية
            memories.sort(key=lambda m: m.get("importance", 0), reverse=True)
            memories = memories[:100]
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(memories, f, ensure_ascii=False, indent=2)
        
        logger.debug(f"💾 Saved memory for user {user_id[:8]}...")
    
    def get_memories(self, user_id: str, limit: int = 10) -> List[MemoryEntry]:
        """الحصول على ذكريات المستخدم"""
        path = self._get_memories_path(user_id)
        
        if not path.exists():
            return []
        
        with open(path, "r", encoding="utf-8") as f:
            memories_data = json.load(f)
        
        # ترتيب حسب الأهمية والحداثة
        memories_data.sort(
            key=lambda m: (m.get("importance", 0), m.get("timestamp", "")),
            reverse=True
        )
        
        return [MemoryEntry(**m) for m in memories_data[:limit]]
    
    def search_memories(self, user_id: str, query: str, limit: int = 5) -> List[MemoryEntry]:
        """بحث في الذكريات"""
        memories = self.get_memories(user_id, limit=100)
        query_lower = query.lower()
        
        # بحث بسيط بالكلمات المفتاحية
        results = []
        for memory in memories:
            if query_lower in memory.content.lower():
                memory.access_count += 1
                memory.last_accessed = datetime.now().isoformat()
                results.append(memory)
        
        return results[:limit]


class SemanticMemory:
    """
    🔍 الذاكرة الدلالية (Semantic)
    
    تستخدم embeddings للبحث الذكي:
    - similar conversations
    - related topics
    - pattern matching
    """
    
    def __init__(self, embedding_model=None):
        self.embedding_model = embedding_model
        self.embeddings_dir = MEMORY_DIR / "embeddings"
        self.embeddings_dir.mkdir(exist_ok=True)
        self._cache: Dict[str, List[float]] = {}
    
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """الحصول على embedding لنص"""
        # للتبسيط، نستخدم hash بسيط
        # في الإنتاج، نستخدم OpenAI/Sentence-Transformers embeddings
        if not text:
            return None
        
        # Hash-based pseudo-embedding
        hash_val = hashlib.sha256(text.encode()).hexdigest()
        embedding = [int(hash_val[i:i+2], 16) / 255.0 for i in range(0, 64, 2)]
        return embedding
    
    def similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """حساب التشابه بين embeddings"""
        if not embedding1 or not embedding2:
            return 0.0
        
        # Cosine similarity
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        norm1 = sum(a * a for a in embedding1) ** 0.5
        norm2 = sum(b * b for b in embedding2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    async def find_similar(self, query: str, memories: List[MemoryEntry], top_k: int = 5) -> List[MemoryEntry]:
        """إيجاد الذكريات المشابهة"""
        query_embedding = await self.get_embedding(query)
        if not query_embedding:
            return []
        
        scored_memories = []
        for memory in memories:
            if memory.embedding:
                score = self.similarity(query_embedding, memory.embedding)
                scored_memories.append((memory, score))
            else:
                # حساب embedding للذكرى
                memory.embedding = await self.get_embedding(memory.content)
                if memory.embedding:
                    score = self.similarity(query_embedding, memory.embedding)
                    scored_memories.append((memory, score))
        
        # ترتيب حسب التشابه
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        
        return [m for m, s in scored_memories[:top_k]]


class MemoryManager:
    """
    🧠 مدير الذاكرة الموحد
    
    يجمع بين جميع أنواع الذاكرة:
    - Short-term
    - Long-term  
    - Semantic
    """
    
    def __init__(self):
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()
        self.semantic = SemanticMemory()
        logger.info("🧠 MemoryManager initialized")
    
    def get_context(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """الحصول على السياق الكامل"""
        profile = self.long_term.get_profile(user_id)
        short_context = self.short_term.get_context(session_id)
        recent_memories = self.long_term.get_memories(user_id, limit=5)
        
        return {
            "user_profile": asdict(profile),
            "conversation": {
                "messages": short_context.messages,
                "topic": short_context.current_topic,
                "active_tools": short_context.active_tools
            },
            "memories": [asdict(m) for m in recent_memories],
            "summary": self.short_term.get_summary(session_id)
        }
    
    def add_interaction(self, user_id: str, session_id: str, role: str, content: str):
        """تسجيل تفاعل"""
        # إضافة للذاكرة القصيرة
        self.short_term.add_message(session_id, role, content)
        
        # تحديث الـ profile
        self.long_term.increment_interactions(user_id)
        
        # حفظ كذكرى مهمة إذا كانت طويلة
        if len(content) > 100 and role == "assistant":
            self.long_term.save_memory(
                user_id,
                content[:500],
                importance=0.6,
                metadata={"role": role, "session": session_id}
            )
    
    def remember_tool_usage(self, user_id: str, session_id: str, tool_name: str):
        """تذكر استخدام أداة"""
        self.short_term.add_active_tool(session_id, tool_name)
        self.long_term.add_favorite_tool(user_id, tool_name)
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """الحصول على تفضيلات المستخدم"""
        profile = self.long_term.get_profile(user_id)
        return {
            "language": profile.language,
            "interests": profile.interests,
            "favorite_tools": profile.favorite_tools,
            **profile.preferences
        }
    
    async def recall(self, user_id: str, query: str) -> Dict[str, Any]:
        """استرجاع المعلومات ذات الصلة"""
        memories = self.long_term.get_memories(user_id, limit=50)
        
        # بحث بالكلمات المفتاحية
        keyword_results = self.long_term.search_memories(user_id, query, limit=3)
        
        # بحث دلالي
        semantic_results = await self.semantic.find_similar(query, memories, top_k=3)
        
        # دمج النتائج
        all_results = []
        seen_ids = set()
        
        for memory in keyword_results + semantic_results:
            if memory.id not in seen_ids:
                all_results.append(memory)
                seen_ids.add(memory.id)
        
        return {
            "memories": [asdict(m) for m in all_results[:5]],
            "count": len(all_results)
        }
    
    def clear_session(self, session_id: str):
        """مسح جلسة"""
        self.short_term.clear(session_id)


# Singleton instance
_memory_manager: Optional[MemoryManager] = None

def get_memory_manager() -> MemoryManager:
    """الحصول على instance من MemoryManager"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
