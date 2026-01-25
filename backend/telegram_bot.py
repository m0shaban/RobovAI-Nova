"""
🤖 RobovAI Nova - Telegram Bot Integration (Professional Edition)
═══════════════════════════════════════════════════════════════

Curated experience featuring only 100% reliable tools.
"""

import logging
import os
from backend.core.llm import llm_client

logger = logging.getLogger("robovai.telegram")

# Safe imports
try:
    from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    logger.warning("python-telegram-bot not installed. Telegram bot disabled.")
    TELEGRAM_AVAILABLE = False

# Import tool registry
try:
    from backend.tools.registry import ToolRegistry
except ImportError:
    ToolRegistry = None

try:
    from backend.core.smart_router import SmartToolRouter
except ImportError:
    SmartToolRouter = None

# ═══════════════════════════════════════════════════════════════════════════
# ⌨️ KEYBOARDS
# ═══════════════════════════════════════════════════════════════════════════

def get_main_keyboard():
    """Return the persistent main menu keyboard"""
    keyboard = [
        [KeyboardButton("🌤️ حالة الطقس"), KeyboardButton("😂 نكتة مصرية")],
        [KeyboardButton("🌍 ترجمة فورية"), KeyboardButton("❓ مساعدة")],
        [KeyboardButton("🛠️ كل الأدوات")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)

# ═══════════════════════════════════════════════════════════════════════════
# 🎯 COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════════════════

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message with persistent keyboard"""
    welcome_text = """
🤖 **أهلاً بك في RobovAI Nova**

أنا مساعدك الذكي المصري 🇪🇬. 
جمعتلك أهم الأدوات اللي هتفيدك وتشتغل معاك 100٪.

👇 **اختار من القائمة تحت:**
    """
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Professional Help Message"""
    help_text = """
📖 **دليل الاستخدام السريع**

أنا هنا عشان أساعدك تنجز شغلك بسرعة. دي الأدوات المضمونة:

🌤️ **الطقس**: اضغط الزر، أو اكتب "الطقس في [المدينة]"
🌍 **الترجمة**: اضغط الزر، أو اكتب "ترجم: [النص]"
😂 **الترفيه**: اضغط زر النكتة لشويه فرفشة
💬 **الشات**: اسألني أي سؤال عام وهجاوبك بذكاء

💡 **نصيحة**: تقدر تكتب وتتكلم معايا بالمصري عادي!
    """
    await update.message.reply_text(help_text, reply_markup=get_main_keyboard(), parse_mode='Markdown')

async def tools_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List ONLY verified tools"""
    text = """
🛠️ **الأدوات المتاحة (Verified Only)**

1️⃣ **أدوات المعلومات:**
• `/weather` - معرفة الطقس
• `/wiki` - بحث في ويكيبيديا
• `/curr` - أسعار العملات

2️⃣ **أدوات تقنية:**
• `/translate` - ترجمة دقيقة
• `/calc` - آلة حاسبة ذكية

3️⃣ **ترفيه:**
• `/joke` - نكت مصرية
• `/quiz` - مسابقة ثقافية

ℹ️ اضغط على أي أداة لتجربتها، أو استخدم الكيبورد للسرعة.
    """
    await update.message.reply_text(text, parse_mode='Markdown')

# ═══════════════════════════════════════════════════════════════════════════
# 💬 MESSAGE HANDLER & ROUTING
# ═══════════════════════════════════════════════════════════════════════════

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages and menu clicks"""
    user_id = str(update.effective_user.id)
    message = update.message.text
    
    logger.info(f"Telegram message from {user_id}: {message}")

    response = ""

    # 1. Handle Menu Clicks
    if message == "🌤️ حالة الطقس":
        response = "📍 من فضلك اكتب اسم المدينة (مثلاً: القاهرة)"
        # Note: In a fuller implementation, we would use ConversationHandler state
    
    elif message == "😂 نكتة مصرية":
        # Execute Joke Tool directly
        from backend.tools.registry import ToolRegistry
        tool_class = ToolRegistry.get_tool("/joke")
        if tool_class:
            res = await tool_class().execute("", user_id)
            response = res.get('output', 'مرة واحد...')
    
    elif message == "🌍 ترجمة فورية":
        response = "🔤 اكتب النص اللي عايز تترجمه مسبوق بكلمة 'ترجم' (مثلاً: ترجم hello world)"
        
    elif message == "❓ مساعدة":
        await help_command(update, context)
        return
        
    elif message == "🛠️ كل الأدوات":
        await tools_command(update, context)
        return

    # 2. Smart Routing for everything else
    if not response:
        # Check for specific patterns
        if "الطقس" in message and len(message.split()) < 2:
             response = "📍 حدد المدينة، مثلاً: الطقس في الإسكندرية"
        
        else:
            # Use Smart Router logic
            # Explicitly BLOCK unreliable tools if detected via keywords?
            # For now, let's trust the router but prioritize text tools
            
            routing_result = await SmartToolRouter.route_message(message, user_id, platform="telegram")
            
            if routing_result['type'] == 'tool':
                # Filter out image generation tools if they slip through
                tool_name = routing_result.get('tool')
                if tool_name in ["/generate_image", "/image"]:
                    response = "⚠️ عذراً، أداة توليد الصور غير متاحة حالياً للتحديث. جرب تطلب نكتة أو معلومة!"
                else:
                    response = routing_result['result'].get('output', 'تم التنفيذ')
            else:
                # LLM Chat
                system_prompt = """أنت RobovAI Nova، مساعد ذكي مصري محترف.
                - ردودك قصيرة ومفيدة.
                - تتحدث بالمصري العامي اللبق.
                - لا تقترح أدوات لا تملكها (مثل الصور حالياً).
                """
                try:
                    response = await llm_client.generate(
                        message,
                        provider="groq",
                        system_prompt=system_prompt
                    )
                except Exception:
                    response = "معلش، السيرفر مشغول شوية. جرب تاني كمان دقيقة."

    # Send Response
    await update.message.reply_text(response, reply_markup=get_main_keyboard())

# ═══════════════════════════════════════════════════════════════════════════
# 🚀 APP SETUP
# ═══════════════════════════════════════════════════════════════════════════

def create_telegram_app():
    """Create and configure Telegram application"""
    if not TELEGRAM_AVAILABLE: return None
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token: return None
    
    application = Application.builder().token(token).build()
    
    # Commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("tools", tools_command))
    
    # Messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    return application

