"""
🤖 RobovAI Nova - Telegram AI Chief of Staff
═══════════════════════════════════════════════════════════════
Professional Assistant for Productivity, Business, and Data Analysis.
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

try:
    from backend.tools.registry import ToolRegistry
except ImportError:
    ToolRegistry = None

try:
    from backend.core.smart_router import SmartToolRouter
except ImportError:
    SmartToolRouter = None

# ═══════════════════════════════════════════════════════════════════════════
# ⌨️ PROFESSIONAL KEYBOARD
# ═══════════════════════════════════════════════════════════════════════════

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Core Logic for 'AI Chief of Staff' - Modern & Professional.
    """
    user_id = str(update.effective_user.id)
    message = update.message.text
    
    # Log for analytics
    logger.info(f"Nova Req [{user_id}]: {message}")
    
    response = ""
    
    # ════════════════════════════════════════════════════════════════════════
    # 1. SMART GRID MENU NAVIGATION
    # ════════════════════════════════════════════════════════════════════════
    if message == "⚡ إجراءات سريعة":
        response = """🚀 **الإجراءات السريعة (Quick Actions)**
        
اختر ما تريد القيام به:
1️⃣ **بحث ويب**: `/search سعر الذهب`
2️⃣ **تحليل سهم**: `/stock NVDA`
3️⃣ **تحويل عملة**: `/convert 100 USD to EGP`
4️⃣ **تحميل فيديو**: `/download [الرابط]`
"""

    elif message == "📂 ملفاتي وتحليلاتي":
        response = """📂 **مركز المستندات والبيانات**
        
يمكنك إرسال الملفات التالية وسأقوم بتحليلها فوراً:
📄 **PDF/Word**: تلخيص واستخراج النقاط الهامة.
📊 **Excel/CSV**: تحليل مالي وإحصائي شامل.
🖼️ **صور**: استخراج نص (OCR) أو تعديل (`/edit`).
"""

    elif message == "🎙️ المساعد الصوتي":
        response = """🎙️ **المساعد الصوتي (Voice Hub)**
        
أرسل **ملاحظة صوتية** (Voice Note) في أي وقت.
- ✅ تفريغ نصي دقيق (Whisper).
- ✅ تلخيص النقاط الهامة.
- ✅ دعم اللهجة المصرية والعربية.
"""

    elif message == "🔍 بحث ذكي":
        response = "🔍 **ماذا تريد أن تعرف؟**\nاكتب `/search` متبوعاً بسؤالك، وسأبحث لك في الإنترنت فوراً."

    elif message == "🌐 بوابة الويب":
        # THE WEB BRIDGE
        web_url = os.getenv("EXTERNAL_URL") or "https://robovai.com"
        await update.message.reply_text(
            f"🌐 **منصة RobovAI Nova المتكاملة**\n\n"
            "للوصول إلى لوحات المعلومات المتقدمة (Dashboards)، إدارة المشاريع، والتقارير التفصيلية، يرجى زيارة بوابتك الشخصية:\n\n"
            f"🔗 {web_url}\n\n"
            "💡 *هنا في تليجرام نركز على السرعة، وهناك نركز على العمق.*",
            disable_web_page_preview=True
        )
        return

    elif message == "🆘 مساعدة / أوامر":
        await help_command(update, context)
        return

    # ════════════════════════════════════════════════════════════════════════
    # 2. SWISS ARMY TOOLS (COMMANDS)
    # ════════════════════════════════════════════════════════════════════════
    
    # [WEB TOOLS]
    elif message.startswith("/search") or message.startswith("بحث"):
        if SearchTool:
             clean = message.replace("/search", "").replace("بحث", "").strip()
             await update.message.reply_text("⏳ **جاري البحث في المصادر الحية...**")
             tool = SearchTool()
             result = await tool.execute(clean, user_id)
             response = result.get("output")

    elif message.startswith("/stock") or message.startswith("سهم"):
        if FinanceTool:
             clean = message.replace("/stock", "").replace("سهم", "").strip()
             await update.message.reply_text("📈 **جاري الاتصال ببيانات البورصة...**")
             tool = FinanceTool()
             result = await tool.execute(clean, user_id)
             response = result.get("output")

    elif message.startswith("/download") or message.startswith("تحميل"):
        if MediaTool:
             clean = message.replace("/download", "").replace("تحميل", "").strip()
             await update.message.reply_text("📥 **جاري معالجة الرابط...**")
             tool = MediaTool()
             result = await tool.execute(clean, user_id)
             response = result.get("output")

    # [VISION TOOLS]
    elif message.startswith("/qr"):
        if QRCodeTool:
            clean = message.replace("/qr", "").strip()
            tool = QRCodeTool()
            res = await tool.execute(clean, user_id)
            if res.get("status") == "success":
                await update.message.reply_photo(res.get("file_content"), caption="📱 **QR Code جاهز.**")
                return
            response = res.get("output")

    elif message.startswith("/edit"):
        USER_EDIT_STATE[user_id] = message.split()[1] if len(message.split()) > 1 else "gray"
        response = "📸 **وضع التعديل:** أرسل الصورة الآن لتطبيق التأثير."
        
    # [OFFICE TOOLS]
    elif message.startswith("/schedule") or message.startswith("جدول"):
        if CalendarEventTool:
            clean = message.replace("/schedule", "").replace("جدول", "").strip()
            tool = CalendarEventTool()
            res = await tool.execute(clean, user_id)
            if res.get("status") == "success":
                # Convert string logic to file logic if needed or tool returns bytes? Tool returns valid ICS string usually.
                # Let's assume tool returns string content for ICS.
                import io
                f = io.BytesIO(res.get("file_content").encode('utf-8'))
                f.name = "meeting.ics"
                await update.message.reply_document(f, caption="📅 **تم جدولة الموعد.**\nإضغط لفتحه في التقويم.")
                return
            response = res.get("output")

    # ════════════════════════════════════════════════════════════════════════
    # 3. AI EXECUTIVE CHAT (MODERN PERSONA)
    # ════════════════════════════════════════════════════════════════════════
    if not response and not message.startswith("/"):
        # Modern Executive Persona Prompt
        system_prompt = """
        أنت (RobovAI Nova)، مدير المكتب الرقمي التنفيذي (AI Chief of Staff).
        - **الشخصية**: ذكي جداً، محترف، حديث، وموجز.
        - **اللهجة**: عربية "بيضاء" (راقية ومفهومة لكل العرب)، بلمسة مصرية خفيفة جداً للود.
        - **الأسلوب**: استخدم النقاط (- Bullet points) دائماً للإجابات الطويلة. استخدم التنسيق (**Bold**) للكلمات المهمة.
        - **المهمة**: مساعدة المستخدم على الإنجاز بأسرع وقت.
        - إذا سأل عن شيء معقد (مثل لوحة بيانات)، وجهه لـ "بوابة الويب" بلباقة.
        """
        
        try:
             await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
             response = await llm_client.generate(message, provider="groq", system_prompt=system_prompt)
        except Exception as e:
             logger.error(f"LLM Error: {e}")
             response = "⚠️ **عذراً،** حدث انقطاع لحظي في الاتصال العصبي. يرجى المحاولة."

    if response:
        await update.message.reply_text(response, reply_markup=get_main_keyboard(), parse_mode="Markdown")

def get_main_keyboard():
    """
    Modern 2x3 Grid Menu for Executive Efficiency.
    """
    keyboard = [
        [KeyboardButton("⚡ إجراءات سريعة"), KeyboardButton("📂 ملفاتي وتحليلاتي")],
        [KeyboardButton("🔍 بحث ذكي"), KeyboardButton("🎙️ المساعد الصوتي")],
        [KeyboardButton("🌐 بوابة الويب"), KeyboardButton("🆘 مساعدة / أوامر")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)

async def safe_reply(update: Update, text: str, reply_markup=None):
    """
    Robust Reply Wrapper:
    1. Tries to send with Markdown.
    2. If it fails (400 Bad Request), sends as Plain Text.
    This prevents the bot from crashing on LLM formatting errors.
    """
    try:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"Markdown Reply Failed: {e}. Falling back to plain text.")
        try:
            # Fallback: Plain text
            await update.message.reply_text(text, reply_markup=reply_markup)
        except Exception as e2:
            logger.error(f"Reply Failed Completely: {e2}")

# ═══════════════════════════════════════════════════════════════════════════
# 🎯 COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════════════════

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Modern Start Screen"""
    welcome_msg = """✨ **أهلاً بك في RobovAI Nova**

أنا مساعدك التنفيذي الشخصي (AI Chief of Staff). 
تم تصميمي لمساعدتك على إدارة أعمالك، تحليل بياناتك، وتنظيم يومك بذكاء.

💡 **ماذا يمكنني أن أفعل؟**
- 🎙️ **تفريغ الملاحظات الصوتية** بدقة.
- 📊 **تحليل ملفات Excel** واستخراج النتائج.
- 📄 **تلخيص العقود والمستندات**.
- 🌐 **البحث في الإنترنت** ومتابعة الأسهم.

👇 **اختر من القائمة بالأسفل للبدء:**
"""
    await safe_reply(update, welcome_msg, reply_markup=get_main_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Detailed Command List"""
    help_text = """🆘 **دليل الأوامر السريعة**

🔹 **البحث والمعلومات:**
`/search [سؤالك]` - بحث حي في جوجل/الويب.
`/stock [رمز]` - سعر السهم (مثال: `/stock AAPL`).
`/convert [قيمة] [من] to [إلى]` - تحويل عملات.

🔹 **الوسائط والملفات:**
`/download [رابط]` - تحميل فيديو.
`/qr [رابط]` - إنشاء كود QR.
`/edit [gray|blur]` - تعديل صور.

🔹 **التنظيم:**
`/schedule [الحدث] | [الوقت]` - إنشاء ملف تقويم.

💡 *نصيحة: يمكنك دائماً التحدث معي باللغة الطبيعية!*
"""
    await safe_reply(update, help_text)

async def tools_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Deprecated in favor of 'Quick Actions' menu, but kept for legacy compat
    await safe_reply(update, "🛠️ انتقلت الأدوات إلى قائمة **إجراءات سريعة** في القائمة الرئيسية.", reply_markup=get_main_keyboard())

# ... (Feature Handlers)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... (Same message parsing logic)
    user_id = str(update.effective_user.id)
    message = update.message.text
    logger.info(f"Nova Req [{user_id}]: {message}")
    response = ""
    
    # ════════════════════════════════════════════════════════════════════════
    # 1. SMART GRID MENU NAVIGATION
    # ════════════════════════════════════════════════════════════════════════
    if message == "⚡ إجراءات سريعة":
        response = """🚀 **الإجراءات السريعة (Quick Actions)**
        
اختر ما تريد القيام به:
1️⃣ **بحث ويب**: `/search سعر الذهب`
2️⃣ **تحليل سهم**: `/stock NVDA`
3️⃣ **تحويل عملة**: `/convert 100 USD to EGP`
4️⃣ **تحميل فيديو**: `/download [الرابط]`
"""

    elif message == "📂 ملفاتي وتحليلاتي":
        response = """📂 **مركز المستندات والبيانات**
        
يمكنك إرسال الملفات التالية وسأقوم بتحليلها فوراً:
📄 **PDF/Word**: تلخيص واستخراج النقاط الهامة.
📊 **Excel/CSV**: تحليل مالي وإحصائي شامل.
🖼️ **صور**: استخراج نص (OCR) أو تعديل (`/edit`).
"""

    elif message == "🎙️ المساعد الصوتي":
        response = """🎙️ **المساعد الصوتي (Voice Hub)**
        
أرسل **ملاحظة صوتية** (Voice Note) في أي وقت.
- ✅ تفريغ نصي دقيق (Whisper).
- ✅ تلخيص النقاط الهامة.
- ✅ دعم اللهجة المصرية والعربية.
"""

    elif message == "🔍 بحث ذكي":
        response = "🔍 **ماذا تريد أن تعرف؟**\nاكتب `/search` متبوعاً بسؤالك، وسأبحث لك في الإنترنت فوراً."

    elif message == "🌐 بوابة الويب":
        # THE WEB BRIDGE
        web_url = os.getenv("EXTERNAL_URL") or "https://robovai.com"
        await safe_reply(update, 
            f"🌐 **منصة RobovAI Nova المتكاملة**\n\n"
            "للوصول إلى لوحات المعلومات المتقدمة (Dashboards)، إدارة المشاريع، والتقارير التفصيلية، يرجى زيارة بوابتك الشخصية:\n\n"
            f"🔗 {web_url}\n\n"
            "💡 *هنا في تليجرام نركز على السرعة، وهناك نركز على العمق.*"
        )
        return

    elif message == "🆘 مساعدة / أوامر":
        await help_command(update, context)
        return

    # ════════════════════════════════════════════════════════════════════════
    # 2. SWISS ARMY TOOLS (COMMANDS)
    # ════════════════════════════════════════════════════════════════════════
    
    # [WEB TOOLS]
    elif message.startswith("/search") or message.startswith("بحث"):
        if SearchTool:
             clean = message.replace("/search", "").replace("بحث", "").strip()
             await update.message.reply_text("⏳ **جاري البحث في المصادر الحية...**")
             tool = SearchTool()
             result = await tool.execute(clean, user_id)
             response = result.get("output")

    elif message.startswith("/stock") or message.startswith("سهم"):
        if FinanceTool:
             clean = message.replace("/stock", "").replace("سهم", "").strip()
             await update.message.reply_text("📈 **جاري الاتصال ببيانات البورصة...**")
             tool = FinanceTool()
             result = await tool.execute(clean, user_id)
             response = result.get("output")

    elif message.startswith("/download") or message.startswith("تحميل"):
        if MediaTool:
             clean = message.replace("/download", "").replace("تحميل", "").strip()
             await update.message.reply_text("📥 **جاري معالجة الرابط...**")
             tool = MediaTool()
             result = await tool.execute(clean, user_id)
             response = result.get("output")

    # [VISION TOOLS]
    elif message.startswith("/qr"):
        if QRCodeTool:
            clean = message.replace("/qr", "").strip()
            tool = QRCodeTool()
            res = await tool.execute(clean, user_id)
            if res.get("status") == "success":
                await update.message.reply_photo(res.get("file_content"), caption="📱 **QR Code جاهز.**")
                return
            response = res.get("output")

    elif message.startswith("/edit"):
        USER_EDIT_STATE[user_id] = message.split()[1] if len(message.split()) > 1 else "gray"
        response = "📸 **وضع التعديل:** أرسل الصورة الآن لتطبيق التأثير."
        
    # [OFFICE TOOLS]
    elif message.startswith("/schedule") or message.startswith("جدول"):
        if CalendarEventTool:
            clean = message.replace("/schedule", "").replace("جدول", "").strip()
            tool = CalendarEventTool()
            res = await tool.execute(clean, user_id)
            if res.get("status") == "success":
                import io
                f = io.BytesIO(res.get("file_content").encode('utf-8'))
                f.name = "meeting.ics"
                await update.message.reply_document(f, caption="📅 **تم جدولة الموعد.**\nإضغط لفتحه في التقويم.")
                return
            response = res.get("output")

    # ════════════════════════════════════════════════════════════════════════
    # 3. AI EXECUTIVE CHAT (MODERN PERSONA)
    # ════════════════════════════════════════════════════════════════════════
    if not response and not message.startswith("/"):
        # Modern Executive Persona Prompt
        system_prompt = """
        أنت (RobovAI Nova)، مدير المكتب الرقمي التنفيذي (AI Chief of Staff).
        - **الشخصية**: ذكي جداً، محترف، حديث، وموجز.
        - **الأسلوب**: استخدم النقاط دائماً. تحاشى الرموز الغريبة التي تكسر التنسيق. استخدم (**) للعناوين.
        - **المهمة**: مساعدة المستخدم على الإنجاز بأسرع وقت.
        """
        
        try:
             await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
             response = await llm_client.generate(message, provider="groq", system_prompt=system_prompt)
        except Exception as e:
             logger.error(f"LLM Error: {e}")
             response = "⚠️ **عذراً،** حدث انقطاع لحظي في الاتصال العصبي. يرجى المحاولة."

    if response:
        await safe_reply(update, response, reply_markup=get_main_keyboard())

# ═══════════════════════════════════════════════════════════════════════════
# 🚀 APP SETUP
# ═══════════════════════════════════════════════════════════════════════════

def create_telegram_app():
    """Create and configure Telegram application"""
    if not TELEGRAM_AVAILABLE: return None
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token: return None
    
    try:
        application = Application.builder().token(token).build()
        
        # Commands
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("tools", tools_command))
        
        # Media Handlers (New)
        application.add_handler(MessageHandler(filters.Document.ALL, handle_document_upload))
        application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice_note))
        
        # Text Message Handler
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        return application
    except Exception as e:
        logger.error(f"Failed to build Telegram App: {e}")
        return None
