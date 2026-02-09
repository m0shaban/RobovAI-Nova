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
    # 👋 Greetings - Arabic
    "hi": "أهلاً! 👋 أنا **نوفا**، مساعدك الذكي من RobovAI.\n\nكيف أقدر أساعدك النهاردة؟ جرب تقولي:\n- 🎨 ارسم صورة\n- 💻 اكتب كود\n- 📊 حلل بيانات\n- ❓ أو اسألني أي سؤال!",
    "hello": "Hey there! 👋 I'm **Nova**, your AI assistant by RobovAI.\n\nWhat can I help you with?\n- 🎨 Generate images\n- 💻 Write code\n- 📊 Analyze data\n- ❓ Or just ask me anything!",
    "مرحبا": "أهلاً وسهلاً! 🌟 أنا **نوفا**، جاهز أساعدك.\n\nقولي إيه اللي محتاجه وهنفذه فوراً! 🚀",
    "مرحبا بيك": "أهلاً بيك! 🌟 أنا نوفا، إزيك النهاردة؟ محتاج حاجة؟",
    "ازيك": "كويس الحمد لله! 😊 إنت إزيك؟\n\nقولي أساعدك في إيه النهاردة؟",
    "إزيك": "كويس الحمد لله! 😊 إنت إزيك؟\n\nقولي أساعدك في إيه النهاردة؟",
    "ازاي": "كويس! 😊 إنت عامل إيه؟ عايز أساعدك في إيه؟",
    "كيف حالك": "بخير الحمد لله! 😊 شكراً على سؤالك. كيف أقدر أخدمك؟",
    "عامل ايه": "تمام الحمد لله! 💪 إنت عامل إيه؟ محتاج مساعدة في حاجة؟",
    "اهلا": "أهلاً بيك! 🌟 أنا **نوفا** مساعدك الذكي.\n\nقولي إيه اللي أقدر أعمله لك! 🚀",
    "هاي": "هاي! 👋 أنا نوفا. إزيك؟ محتاج حاجة؟",
    "hey": "Hey! 👋 I'm Nova. What can I do for you today?",
    "سلام": "وعليكم السلام! ✨ أنا نوفا، جاهز أساعدك.",
    "السلام عليكم": "وعليكم السلام ورحمة الله! ✨ أنا **نوفا**، كيف أقدر أخدمك؟",
    # 🙏 Thanks
    "شكرا": "العفو! 🙏 دا واجبي. لو محتاج أي حاجة تانية، أنا هنا دايماً! 💪",
    "شكراً": "العفو! 🙏 لو محتاج أي حاجة تانية، أنا هنا.",
    "thanks": "You're welcome! 🙏 Let me know if you need anything else.",
    "thank you": "You're welcome! 🙏 Happy to help anytime!",
    "تسلم": "تسلم إنت! 🙏 أي وقت تحتاجني هتلاقيني.",
    "الله يعطيك العافيه": "ويعافيك! 🙏 خدمتك واجب. محتاج حاجة تانية؟",
    # 👋 Farewell
    "bye": "مع السلامة! 👋 بالتوفيق!",
    "باي": "مع السلامة! 👋 لو محتاج حاجة تاني ارجعلي. نورتني! 🌟",
    "مع السلامه": "مع السلامة! 👋 نورتنا. أي وقت ارجعلي!",
    "وداعا": "إلى اللقاء! 👋 بالتوفيق يا بطل!",
    # 🤖 Identity
    "من انت": "أنا **نوفا** 🤖 — مساعدك الذكي من **RobovAI Solutions**!\n\n**قدراتي** (99+ أداة):\n\n🎨 **إبداعية:** توليد صور AI، تصميم عروض تقديمية\n💻 **برمجة:** كتابة أكواد بكل اللغات، إنشاء صفحات HTML، مواقع كاملة\n📄 **ملفات:** تحليل PDF، Excel، تحويل ملفات\n🌐 **بحث:** ويكيبيديا، أخبار، DuckDuckGo\n📊 **أعمال:** حساب ROI، دراسة جدوى، تحليل بيانات\n🎵 **صوت:** تحويل صوت لنص والعكس\n🔧 **أدوات:** QR codes، حاسبة، تحويل عملات\n\nجرب قولي أي حاجة! 🚀",
    "what can you do": "I'm **Nova** 🤖 — your AI assistant from **RobovAI Solutions**!\n\n**My capabilities** (99+ tools):\n\n🎨 **Creative:** AI image generation, presentations\n💻 **Coding:** Write code, HTML pages, full websites\n📄 **Files:** PDF, Excel analysis\n🌐 **Search:** Wikipedia, news, DuckDuckGo\n📊 **Business:** ROI calculator, feasibility studies\n🎵 **Audio:** Speech-to-text & text-to-speech\n🔧 **Utils:** QR codes, calculator, currency converter\n\nTry asking me anything! 🚀",
    "ايه اللي تقدر تعمله": "أنا **نوفا** 🤖 وعندي أكتر من **99 أداة**:\n\n🎨 **إبداعية:** توليد صور، تصميم عروض تقديمية، إنشاء صفحات HTML\n💻 **برمجة:** كتابة أكواد بكل اللغات، شرح كود، debugging\n📄 **ملفات:** تحليل PDF، تفريغ صوت، تحويل ملفات\n🌐 **بحث:** ويكيبيديا، أخبار، ترجمة\n📊 **أعمال:** حساب ROI، تحليل جدوى، بيانات\n🎵 **صوت:** تحويل صوت لنص\n🔧 **أدوات:** QR codes، حاسبة متقدمة، تحويل عملات\n\n**جرب وقولي إيه اللي عايزه!** 🚀",
    "انت ايه": "أنا **نوفا** 🤖 — ذكاء اصطناعي متقدم من RobovAI!\nعندي 99+ أداة. جرب اسألني أي حاجة!",
    "بتعمل ايه": "أنا **نوفا** 🤖 بأعمل حاجات كتير:\n\n🎨 بأولّد صور AI\n💻 بأكتب أكواد\n📊 بأحلل بيانات\n🌐 بأبحث على النت\n📄 بأحلل ملفات\n⚡ و99+ خدمة تانية!\n\nجرب اسألني! 🚀",
    # 💡 Tips
    "مساعده": 'طبعاً! 🌟 أنا هنا عشان أساعدك.\n\n**جرب تقولي:**\n- 🎨 "ارسم صورة قطة في الفضاء"\n- 💻 "اكتبلي كود HTML لصفحة هبوط"\n- 📊 "حلل جدوى مشروع"\n- 🌤️ "الطقس في القاهرة"\n- 😂 "قولي نكتة"\n\nأو اكتب أي سؤال! 🚀',
    "help": 'Sure! 🌟 Here\'s what I can do:\n\n- 🎨 "Generate an image of..."\n- 💻 "Write HTML code for..."\n- 📊 "Analyze feasibility of..."\n- 🌤️ "Weather in Cairo"\n- 😂 "Tell me a joke"\n\nOr just ask me anything! 🚀',
}


def _normalize_key(text: str) -> str:
    """Normalize user input for cache lookup."""
    return (
        text.strip()
        .lower()
        .replace("؟", "")
        .replace("?", "")
        .replace("!", "")
        .replace(".", "")
        .strip()
    )


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
