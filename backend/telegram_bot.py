"""
🤖 RobovAI Nova - Telegram Bot Integration
═══════════════════════════════════════════════════════════════

Full-featured Telegram bot with:
- Menu commands
- Inline keyboards
- Rich media support
- Integration with 112 tools
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from backend.tools.registry import ToolRegistry
from backend.core.smart_router import SmartToolRouter
import logging
import os

logger = logging.getLogger("robovai.telegram")

# ═══════════════════════════════════════════════════════════════════════════
# 🎯 BOT COMMANDS
# ═══════════════════════════════════════════════════════════════════════════

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message with inline keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("🛠️ قائمة الأدوات", callback_data="tools"),
            InlineKeyboardButton("❓ المساعدة", callback_data="help")
        ],
        [
            InlineKeyboardButton("🎨 توليد صورة", callback_data="image"),
            InlineKeyboardButton("🌤️ الطقس", callback_data="weather")
        ],
        [
            InlineKeyboardButton("🌍 ترجمة", callback_data="translate"),
            InlineKeyboardButton("😂 نكتة", callback_data="joke")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = """
🤖 **أهلاً بك في RobovAI Nova!**

أنا مساعدك الذكي المصري 🇪🇬 مع **112 أداة قوية** في خدمتك!

📋 **استخدمني بسهولة:**
• اكتب أي سؤال أو طلب
• استخدم الأزرار أدناه
• أو اكتب `/tools` لرؤية كل الأدوات

🚀 **جرب الآن:** اكتب "ولد صورة روبوت" أو "الطقس في القاهرة"
    """
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help message"""
    help_text = """
📖 **دليل الاستخدام**

🎯 **الأوامر الأساسية:**
/start - بدء المحادثة
/help - عرض المساعدة
/tools - قائمة الأدوات (112)
/menu - القائمة الرئيسية

🛠️ **أدوات شائعة:**
/weather [مدينة] - الطقس
/image [وصف] - توليد صورة
/translate [نص] - ترجمة
/joke - نكتة
/quiz - اختبار

💡 **نصائح:**
• يمكنك الكتابة بالعربي أو الإنجليزي
• البوت يفهم طلبك تلقائياً
• جرب: "ولد صورة قطة" أو "الطقس في الإسكندرية"
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def tools_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all tools with categories"""
    tools = list(ToolRegistry.list_tools())
    
    # Group by category
    categories = {
        "🎨 إبداعية": ["/generate_image", "/unsplash", "/pexels", "/meme"],
        "🌍 ترجمة ولغات": ["/translate_egy", "/grammar", "/synonym"],
        "🌤️ معلومات": ["/weather", "/wiki", "/definition", "/country"],
        "💻 برمجة": ["/code_fix", "/sql", "/regex", "/explain_code"],
        "😂 ترفيه": ["/joke", "/roast", "/rizz", "/trivia", "/quiz"],
        "📊 بيانات": ["/chart", "/diagram", "/quickchart"],
        "🔧 أدوات": ["/qr", "/password", "/uuid", "/hash", "/base64"]
    }
    
    text = "🛠️ **الأدوات المتاحة (112 أداة)**\n\n"
    
    for category, tool_list in categories.items():
        text += f"\n**{category}**\n"
        for tool in tool_list:
            if tool in tools:
                text += f"• {tool}\n"
        
    text += f"\n\n💡 **المزيد:** استخدم `/help` للتفاصيل"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu"""
    await start_command(update, context)

# ═══════════════════════════════════════════════════════════════════════════
# 💬 MESSAGE HANDLER
# ═══════════════════════════════════════════════════════════════════════════

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all text messages"""
    user_id = str(update.effective_user.id)
    message = update.message.text
    
    logger.info(f"Telegram message from {user_id}: {message}")
    
    # Use Smart Router to detect tool
    routing_result = await SmartToolRouter.route_message(message, user_id, platform="telegram")
    
    if routing_result['type'] == 'tool':
        # Tool detected
        tool_result = routing_result['result']
        response = tool_result.get('output', 'تم التنفيذ')
        
        # Send response
        await update.message.reply_text(response, parse_mode='Markdown')
        
    else:
        # General chat - use LLM
        from backend.core.llm import llm_client
        
        system_prompt = """أنت RobovAI Nova، مساعد ذكي مصري ودود.
        - تتحدث بالمصري العامي
        - تساعد المستخدمين بأدب واحترافية
        - لديك 112 أداة قوية"""
        
        try:
            response = await llm_client.generate(
                message,
                provider="groq",
                system_prompt=system_prompt
            )
            await update.message.reply_text(response)
        except Exception as e:
            logger.error(f"LLM error: {e}")
            await update.message.reply_text("عذراً، حدث خطأ. حاول مرة أخرى.")

# ═══════════════════════════════════════════════════════════════════════════
# 🔘 CALLBACK HANDLER (Inline Keyboards)
# ═══════════════════════════════════════════════════════════════════════════

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    
    action = query.data
    
    if action == "tools":
        await tools_command(update, context)
    elif action == "help":
        await help_command(update, context)
    elif action == "image":
        await query.message.reply_text("🎨 اكتب وصف الصورة اللي عايز أولدها:")
    elif action == "weather":
        await query.message.reply_text("🌤️ اكتب اسم المدينة:")
    elif action == "translate":
        await query.message.reply_text("🌍 اكتب النص اللي عايز تترجمه:")
    elif action == "joke":
        # Execute joke tool
        from backend.tools.registry import ToolRegistry
        tool_class = ToolRegistry.get_tool("/joke")
        if tool_class:
            tool = tool_class()
            result = await tool.execute("", str(query.from_user.id))
            await query.message.reply_text(result.get('output', ''))

# ═══════════════════════════════════════════════════════════════════════════
# 🚀 BOT INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════

async def setup_bot_commands(application: Application):
    """Setup bot menu commands"""
    commands = [
        BotCommand("start", "بدء المحادثة"),
        BotCommand("help", "المساعدة"),
        BotCommand("tools", "قائمة الأدوات"),
        BotCommand("menu", "القائمة الرئيسية"),
        BotCommand("weather", "الطقس"),
        BotCommand("image", "توليد صورة"),
        BotCommand("translate", "ترجمة"),
        BotCommand("joke", "نكتة"),
    ]
    await application.bot.set_my_commands(commands)

def create_telegram_app():
    """Create and configure Telegram application"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN not set. Telegram bot disabled.")
        return None
    
    # Create application
    application = Application.builder().token(token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("tools", tools_command))
    application.add_handler(CommandHandler("menu", menu_command))
    
    # Message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Callback handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Setup commands
    application.post_init = setup_bot_commands
    
    logger.info("✅ Telegram bot initialized")
    
    return application
