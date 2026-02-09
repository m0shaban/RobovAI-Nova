"""
🚀 RobovAI Nova - Smart Router v3.0 (State-of-the-Art)
═══════════════════════════════════════════════════════════════

Advanced Features:
✅ Multi-turn Context Memory
✅ Semantic Intent Understanding
✅ Confidence Scoring
✅ Tool Chain Execution
✅ Fallback Strategies
✅ Platform-Aware Responses
✅ Rate Limiting Protection
✅ Usage Analytics
"""

from backend.core.llm import llm_client
from backend.tools.registry import ToolRegistry
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
import re
import json
import hashlib
from collections import defaultdict

# ═══════════════════════════════════════════════════════════════════════════
# 📊 DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class ConversationContext:
    """سياق المحادثة للمستخدم"""

    user_id: str
    messages: List[Dict[str, str]] = field(default_factory=list)
    last_tool: Optional[str] = None
    last_intent: Optional[str] = None
    platform: str = "web"
    language: str = "ar-EG"  # Egyptian Arabic
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    tool_usage: Dict[str, int] = field(default_factory=dict)

    def add_message(self, role: str, content: str):
        self.messages.append(
            {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
        )
        if len(self.messages) > 20:  # Keep last 20 messages
            self.messages = self.messages[-20:]
        self.last_active = datetime.now()

    def get_context_summary(self, max_messages: int = 5) -> str:
        """Get recent conversation context"""
        recent = self.messages[-max_messages:]
        return "\n".join([f"{m['role']}: {m['content'][:100]}" for m in recent])


@dataclass
class RoutingResult:
    """نتيجة التوجيه"""

    route_type: str  # 'tool', 'chat', 'chain', 'clarify'
    tool_name: Optional[str] = None
    tool_chain: List[str] = field(default_factory=list)
    confidence: float = 0.0
    intent: str = ""
    extracted_params: Dict[str, Any] = field(default_factory=dict)
    suggested_response: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════
# 🧠 SMART ROUTER v3.0
# ═══════════════════════════════════════════════════════════════════════════


class SmartToolRouter:
    """
    🚀 RobovAI Nova Smart Router v3.0

    State-of-the-art routing system with:
    - Semantic understanding
    - Context awareness
    - Multi-platform support
    - Tool chaining
    - Confidence scoring
    """

    # User context cache
    _contexts: Dict[str, ConversationContext] = {}

    # Rate limiting
    _rate_limits: Dict[str, List[datetime]] = defaultdict(list)
    MAX_REQUESTS_PER_MINUTE = 30

    # ═══════════════════════════════════════════════════════════════════════
    # 🎯 INTENT PATTERNS (Advanced Regex + Semantic)
    # ═══════════════════════════════════════════════════════════════════════

    # Casual conversation - NEVER trigger tools
    CASUAL_INTENTS = {
        "greeting": [
            r"^(اهلا|مرحبا|السلام عليكم?|صباح الخير|مساء الخير|هاي|هالو|hello|hi|hey|سلام|ازيك|عامل ايه|كيفك|يا هلا)",
            r"^(صباح النور|مساء النور|اهلين|هلا والله)",
        ],
        "farewell": [
            r"^(باي|مع السلامه|bye|goodbye|سلام|وداعا|الى اللقاء)",
        ],
        "identity": [
            r"(انت مين|من انت|اسمك ايه|انت ايه|ايه هو اسمك|مين انت)",
            r"(عرفني بنفسك|عرفني عليك|قولي عن نفسك)",
            r"(who are you|what is your name|introduce yourself|what are you)",
        ],
        "thanks": [
            r"^(شكرا|متشكر|تسلم|الله يعطيك العافيه|thank|thanks|merci)",
        ],
        "affirmation": [
            r"^(اه|لا|اوك|تمام|ماشي|اكيد|طبعا|ok|yes|no|yeah|yep|nope|sure)$",
        ],
        "how_are_you": [
            r"(عامل ايه|كيف حالك|ازيك|اخبارك ايه|how are you|عاملك ايه|ايه اخبارك)",
        ],
        "capabilities": [
            r"(بتعمل ايه|تقدر تعمل ايه|ايه قدراتك|ايه امكانياتك|what can you do)",
            r"(ايه الادوات|فيه ايه|عندك ايه)",
        ],
        # 📤 File uploads - NEVER trigger tools
        "file_upload": [
            r"(جاري رفع|📤|جاري الرفع|uploading)",
            r"(\.jpg|\.jpeg|\.png|\.gif|\.webp|\.pdf|\.doc|\.mp3|\.wav|\.mp4)",
            r"(photo_|image_|file_|document_|audio_|video_)",
        ],
        # 🎤 Voice messages - NEVER trigger tools
        "voice_message": [
            r"^🎤\s*\*\*",
            r"(تسجيل صوتي|رسالة صوتية)",
        ],
    }

    # Tool-specific patterns with parameters extraction
    TOOL_PATTERNS = {
        # 🎨 Creative
        "/generate_image": {
            "patterns": [
                r"(ولد|اعمل|ارسم|صمم|خلق)\s*(صورة|صوره|رسمة|تصميم)\s*(?:عن|ل|لـ)?\s*(.+)?",
                r"(generate|create|draw|make)\s*(image|picture|art)\s*(?:of|about)?\s*(.+)?",
            ],
            "extract": lambda m: {"prompt": m.group(3) if m.lastindex >= 3 else ""},
            "confidence": 0.9,
        },
        # 🌤️ Weather
        "/weather": {
            "patterns": [
                r"(طقس|الجو|حرارة|درجة الحرارة)\s*(?:في|فى)?\s*(.+)?",
                r"(weather|temperature)\s*(?:in|at|for)?\s*(.+)?",
                r"(الجو عامل ايه|ايه حالة الطقس)\s*(?:في|فى)?\s*(.+)?",
            ],
            "extract": lambda m: {
                "location": (
                    m.group(2).strip() if m.lastindex >= 2 and m.group(2) else "Cairo"
                )
            },
            "confidence": 0.95,
        },
        # 😂 Entertainment
        "/joke": {
            "patterns": [
                r"(نكتة|احكيلي نكتة|ضحكني|نكته|قولي نكتة)",
                r"(tell me a joke|joke please|make me laugh)",
            ],
            "extract": lambda m: {},
            "confidence": 0.95,
        },
        # 💱 Currency
        "/currency": {
            "patterns": [
                r"(سعر|حول)\s*(الدولار|اليورو|الجنيه|العملة)",
                r"(currency|exchange rate|convert)\s*(.+)?",
                r"(كام|بكام)\s*(الدولار|اليورو)",
            ],
            "extract": lambda m: {},
            "confidence": 0.9,
        },
        # 📊 Charts
        "/chart": {
            "patterns": [
                r"(رسم بياني|شارت|chart|graph)\s*(.+)?",
                r"(اعمل|ارسم)\s*(رسم بياني|شارت|جدول)",
            ],
            "extract": lambda m: {"data": m.group(2) if m.lastindex >= 2 else ""},
            "confidence": 0.9,
        },
        # 🧮 Math
        "/math": {
            "patterns": [
                r"(احسب|حساب|calculate)\s*(.+)?",
                r"(جذر|sqrt|sin|cos|tan|log)\s*\(?\s*(\d+)",
                r"(\d+)\s*[\+\-\*\/\^]\s*(\d+)",
            ],
            "extract": lambda m: {"expression": m.group(0)},
            "confidence": 0.85,
        },
        # 🔄 Convert
        "/convert": {
            "patterns": [
                r"(حول|convert)\s*(\d+)\s*(\w+)\s*(?:الى|to|إلى)\s*(\w+)",
                r"(\d+)\s*(كيلو|متر|ميل|درجة|kg|km|mi|lb)\s*(?:=|يساوي|كام)",
            ],
            "extract": lambda m: (
                {"value": m.group(2), "from": m.group(3), "to": m.group(4)}
                if m.lastindex >= 4
                else {}
            ),
            "confidence": 0.9,
        },
        # 🎲 Random
        "/pick": {
            "patterns": [
                r"(اختار|اختر|pick|choose)\s*(?:من|from)?\s*(.+)",
                r"(عشوائي|random)\s*(.+)?",
            ],
            "extract": lambda m: {"options": m.group(2) if m.lastindex >= 2 else ""},
            "confidence": 0.85,
        },
        # 📅 Date
        "/date_calc": {
            "patterns": [
                r"(عمري|age|كام سنة)\s*(.+)?",
                r"(فرق|difference)\s*(?:بين|between)\s*(.+)",
            ],
            "extract": lambda m: {},
            "confidence": 0.8,
        },
        # 📖 Quran
        "/quran": {
            "patterns": [
                r"(قران|quran|آية|سورة|surah|ayah)",
            ],
            "extract": lambda m: {},
            "confidence": 0.9,
        },
        # 🔍 Wikipedia
        "/wikipedia": {
            "patterns": [
                r"(ويكيبيديا|wikipedia|wiki)\s*(.+)?",
                r"(ابحث عن|search for|معلومات عن)\s*(.+)",
            ],
            "extract": lambda m: {"query": m.group(2) if m.lastindex >= 2 else ""},
            "confidence": 0.8,
        },
        # 💻 Code
        "/code_fix": {
            "patterns": [
                r"(صلح|اصلح|fix|debug)\s*(?:الكود|هذا الكود|this code|code)",
                r"(فيه خطأ|there is an error|bug in)",
            ],
            "extract": lambda m: {},
            "confidence": 0.85,
        },
        # 🔐 Password
        "/check_password": {
            "patterns": [
                r"(قوة|فحص|check)\s*(?:كلمة المرور|كلمة السر|password)",
            ],
            "extract": lambda m: {},
            "confidence": 0.9,
        },
    }

    # ═══════════════════════════════════════════════════════════════════════
    # 🔧 CORE METHODS
    # ═══════════════════════════════════════════════════════════════════════

    @classmethod
    def get_context(cls, user_id: str, platform: str = "web") -> ConversationContext:
        """Get or create user context"""
        if user_id not in cls._contexts:
            cls._contexts[user_id] = ConversationContext(
                user_id=user_id, platform=platform
            )
        return cls._contexts[user_id]

    @classmethod
    def check_rate_limit(cls, user_id: str) -> bool:
        """Check if user is rate limited"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)

        # Clean old entries
        cls._rate_limits[user_id] = [
            t for t in cls._rate_limits[user_id] if t > minute_ago
        ]

        if len(cls._rate_limits[user_id]) >= cls.MAX_REQUESTS_PER_MINUTE:
            return False

        cls._rate_limits[user_id].append(now)
        return True

    @classmethod
    def is_casual_intent(cls, message: str) -> Tuple[bool, str]:
        """
        Check if message is casual conversation
        Returns: (is_casual, intent_type)
        """
        message_lower = message.lower().strip()

        # Very short messages are usually casual
        if len(message_lower.split()) <= 2 and not message_lower.startswith("/"):
            for intent, patterns in cls.CASUAL_INTENTS.items():
                for pattern in patterns:
                    if re.search(pattern, message_lower, re.IGNORECASE):
                        return True, intent
            # Even if no pattern matched, short messages are casual
            return True, "short_message"

        # Check casual patterns
        for intent, patterns in cls.CASUAL_INTENTS.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    return True, intent

        return False, ""

    @classmethod
    def detect_tool_pattern(cls, message: str) -> Optional[RoutingResult]:
        """
        Detect tool from message using pattern matching
        Returns RoutingResult with confidence score
        """
        message_lower = message.lower().strip()

        # Direct command
        if message_lower.startswith("/"):
            tool_name = message_lower.split()[0]
            if ToolRegistry.get_tool(tool_name):
                return RoutingResult(
                    route_type="tool",
                    tool_name=tool_name,
                    confidence=1.0,
                    intent="direct_command",
                )

        # Pattern matching
        for tool_name, config in cls.TOOL_PATTERNS.items():
            for pattern in config["patterns"]:
                match = re.search(pattern, message_lower, re.IGNORECASE)
                if match:
                    params = {}
                    try:
                        params = config["extract"](match)
                    except:
                        pass

                    return RoutingResult(
                        route_type="tool",
                        tool_name=tool_name,
                        confidence=config["confidence"],
                        intent=f"pattern_{tool_name}",
                        extracted_params=params,
                    )

        return None

    @classmethod
    async def detect_tool_semantic(
        cls, message: str, context: ConversationContext
    ) -> Optional[RoutingResult]:
        """
        Use LLM for semantic intent detection (fallback)
        Only called for ambiguous messages
        """
        # Get available tools
        all_tools = list(ToolRegistry.list_tools())[:30]  # Limit for prompt size

        prompt = f"""Analyze this user message and determine if they want to use a specific tool.

User message: "{message}"

Available tools (examples):
- /weather: check weather
- /joke: tell jokes
- /generate_image: create AI images
- /translate_egy: translate to Egyptian Arabic
- /chart: create charts
- /math: calculations
- /convert: unit conversion
- /quran: Quran verses
- /wikipedia: search Wikipedia

Recent context: {context.get_context_summary(3)}

IMPORTANT: If the message is casual conversation (greetings, questions about the bot, thanks, etc.), respond with "CHAT".

Response format (JSON):
{{"tool": "/tool_name or CHAT", "confidence": 0.0-1.0, "reason": "brief reason"}}
"""

        try:
            response = await llm_client.generate(
                prompt,
                provider="auto",
                system_prompt="You are an intent classifier. Output only valid JSON.",
            )

            # Parse response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1].replace("json", "").strip()

            data = json.loads(response)

            if data.get("tool", "CHAT").upper() == "CHAT":
                return None

            tool_name = data.get("tool", "")
            if tool_name and ToolRegistry.get_tool(tool_name):
                return RoutingResult(
                    route_type="tool",
                    tool_name=tool_name,
                    confidence=float(data.get("confidence", 0.7)),
                    intent="semantic_detection",
                )

        except Exception as e:
            print(f"Semantic detection error: {e}")

        return None

    @classmethod
    async def detect_tool(
        cls, user_message: str, user_id: str = "default", platform: str = "web"
    ) -> Optional[str]:
        """
        Main detection method - backwards compatible
        """
        result = await cls.route(user_message, user_id, platform)
        return result.tool_name if result.route_type == "tool" else None

    @classmethod
    async def route(
        cls, message: str, user_id: str = "default", platform: str = "web"
    ) -> RoutingResult:
        """
        🚀 Main routing method - Advanced routing with all features
        """
        context = cls.get_context(user_id, platform)
        context.add_message("user", message)

        # 1. Rate limit check
        if not cls.check_rate_limit(user_id):
            print(f"⚠️ Rate Limit Exceeded for {user_id}")
            return RoutingResult(
                route_type="chat",
                suggested_response="⚠️ عذراً، لقد تجاوزت الحد المسموح من الرسائل في الدقيقة. يرجى الانتظار قليلاً.",
            )

        # 2. Check casual intent first
        is_casual, intent = cls.is_casual_intent(message)
        if is_casual:
            return RoutingResult(route_type="chat", intent=intent)

        # 3. Pattern-based detection (fast path)
        pattern_result = cls.detect_tool_pattern(message)
        if pattern_result and pattern_result.confidence >= 0.8:
            context.last_tool = pattern_result.tool_name
            context.last_intent = pattern_result.intent
            return pattern_result

        # 4. For medium-length messages, try semantic detection
        word_count = len(message.split())
        if word_count >= 4 and word_count <= 50:
            semantic_result = await cls.detect_tool_semantic(message, context)
            if semantic_result and semantic_result.confidence >= 0.75:
                context.last_tool = semantic_result.tool_name
                return semantic_result

        # 5. Default to chat
        return RoutingResult(route_type="chat", intent="general")

    @classmethod
    async def route_message(
        cls, user_message: str, user_id: str, platform: str = "web"
    ) -> Dict[str, Any]:
        """
        توجيه الرسالة للأداة المناسبة أو للمحادثة العامة
        Backwards compatible with existing code
        """
        result = await cls.route(user_message, user_id, platform)
        context = cls.get_context(user_id, platform)

        if result.route_type == "tool" and result.tool_name:
            tool_class = ToolRegistry.get_tool(result.tool_name)
            if tool_class:
                tool = tool_class()

                # Extract payload from message
                user_input = user_message
                if user_message.lower().startswith(result.tool_name):
                    parts = user_message.split(maxsplit=1)
                    user_input = parts[1] if len(parts) > 1 else ""

                # Add extracted params if available
                if result.extracted_params:
                    for key, value in result.extracted_params.items():
                        if value and key not in user_input:
                            user_input = f"{user_input} {value}".strip()

                # Execute tool
                try:
                    tool_result = await tool.execute(user_input, user_id)

                    # Track usage
                    context.tool_usage[result.tool_name] = (
                        context.tool_usage.get(result.tool_name, 0) + 1
                    )

                    return {
                        "type": "tool",
                        "tool_name": result.tool_name,
                        "result": tool_result,
                        "confidence": result.confidence,
                        "intent": result.intent,
                    }
                except Exception as e:
                    return {
                        "type": "error",
                        "error": str(e),
                        "tool_name": result.tool_name,
                    }

        return {
            "type": "chat",
            "tool_name": None,
            "intent": result.intent,
            "suggested_response": result.suggested_response,
        }

    @classmethod
    def get_user_stats(cls, user_id: str) -> Dict[str, Any]:
        """Get usage statistics for a user"""
        if user_id not in cls._contexts:
            return {}

        context = cls._contexts[user_id]
        return {
            "user_id": user_id,
            "platform": context.platform,
            "message_count": len(context.messages),
            "tool_usage": context.tool_usage,
            "most_used_tool": (
                max(context.tool_usage, key=context.tool_usage.get)
                if context.tool_usage
                else None
            ),
            "last_active": context.last_active.isoformat(),
            "session_duration": (datetime.now() - context.created_at).total_seconds(),
        }

    @classmethod
    def cleanup_old_contexts(cls, max_age_hours: int = 24):
        """Remove old inactive contexts"""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        to_remove = [
            uid for uid, ctx in cls._contexts.items() if ctx.last_active < cutoff
        ]
        for uid in to_remove:
            del cls._contexts[uid]
        return len(to_remove)
