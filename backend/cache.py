"""
⚡ RobovAI Nova — Response Cache
════════════════════════════════
In-memory TTL cache for common/repeated queries.
Saves LLM tokens by serving cached answers for identical questions.
"""

import hashlib
import time
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("robovai.cache")

# ═══════════════════════════════════════════════════════════════
# 🗃️  In-Memory Cache with TTL
# ═══════════════════════════════════════════════════════════════

_cache: Dict[str, Dict[str, Any]] = {}

# Default TTL = 10 minutes  (configurable)
DEFAULT_TTL = 600

# Max cache entries (LRU eviction when exceeded)
MAX_ENTRIES = 500


# ── Common / predefined responses (no LLM call needed) ─────────
INSTANT_RESPONSES: Dict[str, str] = {
    "hi": "أهلاً! 👋 أنا نوفا، مساعدك الذكي. كيف أقدر أساعدك النهاردة؟",
    "hello": "Hey there! 👋 I'm Nova, your AI assistant. How can I help you today?",
    "مرحبا": "أهلاً وسهلاً! 🌟 أنا نوفا، جاهز أساعدك. قولي إيه اللي محتاجه؟",
    "مرحبا بيك": "أهلاً بيك! 🌟 أنا نوفا، إزيك النهاردة؟ محتاج حاجة؟",
    "ازيك": "كويس الحمد لله! 😊 إنت إزيك؟ محتاج مساعدة في حاجة؟",
    "إزيك": "كويس الحمد لله! 😊 إنت إزيك؟ محتاج مساعدة في حاجة؟",
    "ازاي": "كويس! 😊 إنت عامل إيه؟ عايز أساعدك في إيه؟",
    "كيف حالك": "بخير الحمد لله! 😊 شكراً على سؤالك. كيف أقدر أخدمك؟",
    "شكرا": "العفو! 🙏 لو محتاج أي حاجة تانية، أنا هنا.",
    "شكراً": "العفو! 🙏 لو محتاج أي حاجة تانية، أنا هنا.",
    "thanks": "You're welcome! 🙏 Let me know if you need anything else.",
    "thank you": "You're welcome! 🙏 Happy to help anytime.",
    "اهلا": "أهلاً بيك! 🌟 أنا نوفا مساعدك الذكي. إيه اللي أقدر أعمله لك؟",
    "هاي": "هاي! 👋 أنا نوفا. إزيك؟ محتاج حاجة؟",
    "hey": "Hey! 👋 I'm Nova. What can I do for you today?",
    "سلام": "وعليكم السلام! ✨ أنا نوفا، جاهز أساعدك.",
    "السلام عليكم": "وعليكم السلام ورحمة الله! ✨ أنا نوفا، كيف أقدر أخدمك؟",
    "bye": "مع السلامة! 👋 بالتوفيق!",
    "باي": "مع السلامة! 👋 لو محتاج حاجة تاني ارجعلي.",
    "مع السلامه": "مع السلامة! 👋 نورتنا. أي وقت ارجعلي.",
    "من انت": "أنا **نوفا** 🤖 — مساعدك الذكي من RobovAI!\n\nعندي أكتر من **99 أداة** تقدر تساعدك في:\n- 🎨 توليد صور\n- 💻 كتابة أكواد\n- 📄 تحليل ملفات\n- 🌐 بحث على الإنترنت\n- 📊 عروض تقديمية\n- 🎵 صوتيات\n\nجرب قولي أي حاجة! 🚀",
    "what can you do": "I'm **Nova** 🤖 — your AI assistant from RobovAI!\n\nI have **99+ tools** including:\n- 🎨 Image generation\n- 💻 Code writing\n- 📄 File analysis\n- 🌐 Web search\n- 📊 Presentations\n- 🎵 Audio processing\n\nTry asking me anything! 🚀",
    "ايه اللي تقدر تعمله": "أنا **نوفا** 🤖 وعندي أكتر من **99 أداة**:\n\n🎨 **إبداعية:** توليد صور، تصميم عروض تقديمية\n💻 **برمجة:** كتابة أكواد، شرح كود، إنشاء صفحات HTML\n📄 **ملفات:** تحليل PDF، تحويل ملفات\n🌐 **بحث:** ويكيبيديا، أخبار، ترجمة\n📊 **أعمال:** حساب ROI، تحليل جدوى\n🎵 **صوت:** تحويل صوت لنص\n\nجرب وقولي إيه اللي عايزه! 🚀",
}


def _normalize_key(text: str) -> str:
    """Normalize user input for cache lookup."""
    return text.strip().lower().replace("؟", "").replace("?", "").replace("!", "").replace(".", "").strip()


def get_instant_response(message: str) -> Optional[str]:
    """Check if we have a pre-built response (zero tokens)."""
    key = _normalize_key(message)
    return INSTANT_RESPONSES.get(key)


def _make_hash(message: str, user_id: str) -> str:
    """Create a cache key from message + user context."""
    raw = f"{_normalize_key(message)}|{user_id}"
    return hashlib.md5(raw.encode()).hexdigest()


def get_cached(message: str, user_id: str = "") -> Optional[str]:
    """Return cached response if exists and not expired."""
    # Check instant responses first
    instant = get_instant_response(message)
    if instant:
        return instant

    key = _make_hash(message, user_id)
    entry = _cache.get(key)
    if entry and time.time() < entry["expires"]:
        logger.info(f"⚡ Cache HIT for: {message[:40]}...")
        return entry["response"]

    # Expired — clean up
    if entry:
        del _cache[key]
    return None


def set_cached(message: str, response: str, user_id: str = "", ttl: int = DEFAULT_TTL):
    """Store response in cache with TTL."""
    # Don't cache very short or error responses
    if not response or len(response) < 10 or response.startswith("❌"):
        return

    # Evict oldest if full
    if len(_cache) >= MAX_ENTRIES:
        oldest_key = min(_cache, key=lambda k: _cache[k]["expires"])
        del _cache[oldest_key]

    key = _make_hash(message, user_id)
    _cache[key] = {
        "response": response,
        "expires": time.time() + ttl,
        "created": time.time(),
    }
    logger.info(f"💾 Cached response for: {message[:40]}... (TTL={ttl}s)")


def clear_cache():
    """Clear all cached responses."""
    _cache.clear()
    logger.info("🗑️ Cache cleared")


def cache_stats() -> Dict[str, Any]:
    """Return cache statistics."""
    now = time.time()
    active = sum(1 for v in _cache.values() if now < v["expires"])
    return {
        "total_entries": len(_cache),
        "active_entries": active,
        "instant_responses": len(INSTANT_RESPONSES),
    }
