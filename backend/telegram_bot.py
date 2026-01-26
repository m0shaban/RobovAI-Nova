"""
🤖 RobovAI Nova - Telegram AI Executive Assistant v2.0
═══════════════════════════════════════════════════════════════
Professional AI Chief of Staff - SaaS Ready Edition
"""

import logging
import os
import tempfile
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

logger = logging.getLogger("robovai.telegram")

# Safe imports
try:
    from backend.tools.registry import ToolRegistry
except ImportError:
    ToolRegistry = None
    logger.warning("ToolRegistry not available")

try:
    from backend.core.llm import llm_client
except ImportError:
    llm_client = None
    logger.warning("LLM client not available")

# ═══════════════════════════════════════════════════════════════════════════
# 📊 STATE & NAVIGATION
# ═══════════════════════════════════════════════════════════════════════════

USER_STATE = {}  # Track user menu state

# ═══════════════════════════════════════════════════════════════════════════
# ⌨️ PROFESSIONAL KEYBOARD MENUS
# ═══════════════════════════════════════════════════════════════════════════

def get_main_keyboard():
    """Main Menu - Professional 2x3 Grid"""
    keyboard = [
        [KeyboardButton("🤖 محادثة ذكية"), KeyboardButton("🛠️ الأدوات")],
        [KeyboardButton("📁 ملفاتي"), KeyboardButton("🔍 بحث وبيانات")],
        [KeyboardButton("⚙️ الإعدادات"), KeyboardButton("ℹ️ عن Nova")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)

def get_tools_keyboard():
    """Tools Sub-Menu - Categorized"""
    keyboard = [
        [KeyboardButton("🎨 إبداعية"), KeyboardButton("💼 أعمال")],
        [KeyboardButton("🔧 تقنية"), KeyboardButton("🌐 ويب")],
        [KeyboardButton("🎭 ترفيه"), KeyboardButton("◀️ القائمة الرئيسية")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_creative_tools_keyboard():
    """Creative Tools"""
    keyboard = [
        [KeyboardButton("/generate_image 🎨"), KeyboardButton("/qr 📱")],
        [KeyboardButton("/chart 📊"), KeyboardButton("/diagram 📐")],
        [KeyboardButton("◀️ الأدوات")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_business_tools_keyboard():
    """Business Tools"""
    keyboard = [
        [KeyboardButton("/ask_pdf 📄"), KeyboardButton("/excel 📊")],
        [KeyboardButton("/currency 💱"), KeyboardButton("/stock 📈")],
        [KeyboardButton("◀️ الأدوات")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_dev_tools_keyboard():
    """Developer Tools"""
    keyboard = [
        [KeyboardButton("/code_fix 🔧"), KeyboardButton("/sql 🗄️")],
        [KeyboardButton("/regex 🔤"), KeyboardButton("/json 📋")],
        [KeyboardButton("◀️ الأدوات")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_web_tools_keyboard():
    """Web & Data Tools"""
    keyboard = [
        [KeyboardButton("/search 🔍"), KeyboardButton("/weather 🌤️")],
        [KeyboardButton("/wikipedia 📚"), KeyboardButton("/translate 🌐")],
        [KeyboardButton("◀️ الأدوات")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_fun_tools_keyboard():
    """Fun & Entertainment Tools"""
    keyboard = [
        [KeyboardButton("/joke 😂"), KeyboardButton("/quote 💭")],
        [KeyboardButton("/cat 🐱"), KeyboardButton("/dog 🐕")],
        [KeyboardButton("/fact 💡"), KeyboardButton("◀️ الأدوات")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ═══════════════════════════════════════════════════════════════════════════
# 🛡️ SAFE REPLY WRAPPER
# ═══════════════════════════════════════════════════════════════════════════

async def safe_reply(update: Update, text: str, reply_markup=None, parse_mode="HTML"):
    """Robust reply with automatic fallback"""
    try:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        logger.info(f"Sent message to user {update.effective_user.id}")
    except Exception as e:
        logger.warning(f"HTML failed: {e}. Trying plain text.")
        try:
            await update.message.reply_text(text, reply_markup=reply_markup)
        except Exception as e2:
            logger.error(f"Reply failed: {e2}", exc_info=True)

# ═══════════════════════════════════════════════════════════════════════════
# 🎯 COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════════════════

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Professional Welcome Screen"""
    logger.info(f"User {update.effective_user.id} started the bot")
    
    user_name = update.effective_user.first_name or "مستخدم"
    
    welcome_msg = f"""✨ <b>مرحباً بك في RobovAI Nova</b>

مساعدك التنفيذي الذكي المصمم للأعمال والإنتاجية.

━━━━━━━━━━━━━━━━━━━━

📊 <b>ما يمكنني فعله:</b>

• تحليل المستندات والبيانات
• إنشاء تقارير ورسوم بيانية
• البحث وجمع المعلومات
• معالجة الصوت والصور

━━━━━━━━━━━━━━━━━━━━

اختر من القائمة للبدء 👇
"""
    await safe_reply(update, welcome_msg, reply_markup=get_main_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comprehensive Help"""
    logger.info(f"User {update.effective_user.id} requested help")
    
    help_text = """📖 <b>دليل الاستخدام السريع</b>

━━━━━━━━━━━━━━━━━━━━

<b>🔹 الأوامر الأساسية:</b>
• /start - بدء المحادثة
• /help - عرض المساعدة
• /tools - قائمة الأدوات

<b>🔹 أمثلة سريعة:</b>
• <code>/search أخبار التقنية</code>
• <code>/weather القاهرة</code>
• <code>/generate_image غروب على النيل</code>
• <code>/joke</code>

<b>🔹 معالجة الملفات:</b>
• أرسل <b>ملف PDF</b> ← تحليل وتلخيص
• أرسل <b>ملف Excel</b> ← تحليل البيانات
• أرسل <b>ملاحظة صوتية</b> ← تفريغ نصي

━━━━━━━━━━━━━━━━━━━━

💬 أو اكتب طلبك بلغة طبيعية وسأفهمك تلقائياً!
"""
    await safe_reply(update, help_text, reply_markup=get_main_keyboard())

async def tools_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show tools menu"""
    logger.info(f"User {update.effective_user.id} requested tools")
    
    tools_text = """🛠️ <b>اختر فئة الأدوات</b>

━━━━━━━━━━━━━━━━━━━━

🎨 <b>إبداعية</b> - توليد صور، QR، رسوم بيانية
💼 <b>أعمال</b> - تحليل PDF، Excel، عملات
🔧 <b>تقنية</b> - إصلاح كود، SQL، Regex
🌐 <b>ويب</b> - بحث، طقس، ويكيبيديا
🎭 <b>ترفيه</b> - نكت، حقائق، اقتباسات

━━━━━━━━━━━━━━━━━━━━

اختر فئة من الأزرار بالأسفل 👇
"""
    await safe_reply(update, tools_text, reply_markup=get_tools_keyboard())

# ═══════════════════════════════════════════════════════════════════════════
# 📨 MAIN MESSAGE HANDLER
# ═══════════════════════════════════════════════════════════════════════════

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Core message handler with professional UX"""
    try:
        user_id = str(update.effective_user.id)
        message = update.message.text or ""
        
        logger.info(f"Nova [{user_id}]: {message}")
        
        response = ""
        keyboard = get_main_keyboard()
        
        # ════════════════════════════════════════════════════════════════════════
        # 1. MENU NAVIGATION
        # ════════════════════════════════════════════════════════════════════════
        
        # Main Menu Items
        if message == "🤖 محادثة ذكية":
            response = """🤖 <b>وضع المحادثة الذكية</b>

أنا جاهز للمحادثة! اكتب أي سؤال أو طلب وسأساعدك.

<b>أمثلة:</b>
• "اشرح لي الذكاء الاصطناعي ببساطة"
• "ساعدني في كتابة إيميل رسمي"
• "ما هي أفضل الممارسات في إدارة المشاريع؟"

💬 اكتب رسالتك..."""
        
        elif message == "🛠️ الأدوات":
            await tools_command(update, context)
            return
        
        elif message == "📁 ملفاتي":
            response = """📁 <b>مركز إدارة الملفات</b>

━━━━━━━━━━━━━━━━━━━━

<b>الملفات المدعومة:</b>

📄 <b>PDF</b> - استخراج النص والتلخيص
📊 <b>Excel/CSV</b> - تحليل البيانات
📝 <b>Word</b> - معالجة المستندات
🖼️ <b>صور</b> - استخراج النص (OCR)
🎤 <b>صوت</b> - تفريغ نصي

━━━━━━━━━━━━━━━━━━━━

📤 <b>أرسل ملفك الآن</b> وسأقوم بتحليله تلقائياً!"""
        
        elif message == "🔍 بحث وبيانات":
            response = """🔍 <b>البحث وجمع البيانات</b>

━━━━━━━━━━━━━━━━━━━━

<b>الأوامر المتاحة:</b>

🔎 <code>/search [سؤالك]</code> - بحث في الويب
🌤️ <code>/weather [مدينة]</code> - حالة الطقس
📚 <code>/wikipedia [موضوع]</code> - ويكيبيديا
💱 <code>/currency USD EGP</code> - أسعار العملات
📈 <code>/stock AAPL</code> - أسعار الأسهم

━━━━━━━━━━━━━━━━━━━━

اكتب الأمر المطلوب 👆"""
            keyboard = get_web_tools_keyboard()
        
        elif message == "⚙️ الإعدادات":
            web_url = os.getenv("EXTERNAL_URL") or os.getenv("RENDER_EXTERNAL_URL") or "https://robovai.com"
            response = f"""⚙️ <b>الإعدادات والحساب</b>

━━━━━━━━━━━━━━━━━━━━

👤 <b>معرفك:</b> <code>{user_id}</code>
📱 <b>المنصة:</b> Telegram

🌐 <b>لوحة التحكم الكاملة:</b>
{web_url}

━━━━━━━━━━━━━━━━━━━━

<i>للإعدادات المتقدمة، قم بزيارة بوابة الويب.</i>"""
        
        elif message == "ℹ️ عن Nova":
            response = """ℹ️ <b>عن RobovAI Nova</b>

━━━━━━━━━━━━━━━━━━━━

🤖 <b>Nova</b> هو مساعد ذكاء اصطناعي متقدم 
مصمم للأعمال والإنتاجية.

<b>الميزات:</b>
• 100+ أداة ذكية متكاملة
• تحليل المستندات والبيانات
• توليد صور ورسوم بيانية
• تفريغ الصوت بدقة عالية
• دعم متعدد اللغات

━━━━━━━━━━━━━━━━━━━━

⚡ <b>الإصدار:</b> 2.0 SaaS
🏢 <b>من:</b> RobovAI Solutions
🌐 <b>الموقع:</b> robovai.com"""
        
        # Tools Categories
        elif message == "🎨 إبداعية":
            response = """🎨 <b>الأدوات الإبداعية</b>

<code>/generate_image [وصف]</code> - توليد صورة AI
<code>/qr [نص أو رابط]</code> - إنشاء QR Code
<code>/chart [بيانات]</code> - رسم بياني
<code>/diagram [وصف]</code> - رسم مخطط

اختر أداة من الأزرار 👇"""
            keyboard = get_creative_tools_keyboard()
        
        elif message == "💼 أعمال":
            response = """💼 <b>أدوات الأعمال</b>

<code>/ask_pdf</code> - تحليل ملفات PDF
<code>/excel</code> - معالجة Excel
<code>/currency [عملة]</code> - أسعار العملات
<code>/stock [رمز]</code> - أسعار الأسهم

اختر أداة من الأزرار 👇"""
            keyboard = get_business_tools_keyboard()
        
        elif message == "🔧 تقنية":
            response = """🔧 <b>الأدوات التقنية</b>

<code>/code_fix [كود]</code> - إصلاح الكود
<code>/sql [استعلام]</code> - بناء SQL
<code>/regex [نمط]</code> - اختبار Regex
<code>/json [بيانات]</code> - تنسيق JSON

اختر أداة من الأزرار 👇"""
            keyboard = get_dev_tools_keyboard()
        
        elif message == "🌐 ويب":
            response = """🌐 <b>أدوات الويب والبيانات</b>

<code>/search [سؤال]</code> - بحث ويب
<code>/weather [مدينة]</code> - الطقس
<code>/wikipedia [موضوع]</code> - ويكيبيديا
<code>/translate [نص]</code> - ترجمة

اختر أداة من الأزرار 👇"""
            keyboard = get_web_tools_keyboard()
        
        elif message == "🎭 ترفيه":
            response = """🎭 <b>أدوات الترفيه</b>

<code>/joke</code> - نكتة عشوائية
<code>/quote</code> - اقتباس ملهم
<code>/cat</code> - صورة قطة 🐱
<code>/dog</code> - صورة كلب 🐕
<code>/fact</code> - حقيقة مثيرة

اختر أداة من الأزرار 👇"""
            keyboard = get_fun_tools_keyboard()
        
        # Navigation
        elif message == "◀️ القائمة الرئيسية":
            response = "🏠 العودة للقائمة الرئيسية"
            keyboard = get_main_keyboard()
        
        elif message == "◀️ الأدوات":
            await tools_command(update, context)
            return
        
        # ════════════════════════════════════════════════════════════════════════
        # 2. TOOL COMMANDS
        # ════════════════════════════════════════════════════════════════════════
        elif message.startswith("/") and ToolRegistry:
            parts = message.split(" ", 1)
            command = parts[0].split("_")[0] if "_" in parts[0] else parts[0]  # Handle button format
            command = command.replace(" ", "").split()[0]  # Clean command
            arg = parts[1] if len(parts) > 1 else ""
            
            tool_class = ToolRegistry.get_tool(command)
            if tool_class:
                logger.info(f"Executing tool: {command}")
                try:
                    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
                    tool = tool_class()
                    result = await tool.execute(arg, user_id)
                    response = result.get("output", "✅ تم التنفيذ")
                    logger.info(f"Tool {command} success")
                except Exception as e:
                    logger.error(f"Tool error: {e}", exc_info=True)
                    response = f"❌ خطأ في تنفيذ الأداة: {str(e)[:100]}"
            else:
                response = f"⚠️ الأمر <code>{command}</code> غير متاح.\nاستخدم /help للمساعدة."
        
        # ════════════════════════════════════════════════════════════════════════
        # 3. AI CHAT
        # ════════════════════════════════════════════════════════════════════════
        elif not response:
            system_prompt = """أنت Nova، مساعد ذكاء اصطناعي تنفيذي من RobovAI.

الشخصية:
- محترف وذكي
- ودود بدون مبالغة
- موجز ومنظم

الأسلوب:
- استخدم النقاط للقوائم
- كن مباشراً في الإجابة
- قدم معلومات عملية

اللغة:
- عربية فصحى مبسطة
- تجنب العامية المفرطة"""
            
            try:
                await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
                if llm_client:
                    response = await llm_client.generate(message, provider="groq", system_prompt=system_prompt)
                else:
                    response = "⚠️ النظام غير متاح حالياً. يرجى المحاولة لاحقاً."
            except Exception as e:
                logger.error(f"LLM error: {e}", exc_info=True)
                response = "⚠️ حدث خطأ. يرجى المحاولة مرة أخرى."
        
        # Send response
        if response:
            await safe_reply(update, response, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
        await safe_reply(update, "⚠️ حدث خطأ تقني. يرجى المحاولة لاحقاً.")

# ═══════════════════════════════════════════════════════════════════════════
# 📎 DOCUMENT HANDLER
# ═══════════════════════════════════════════════════════════════════════════

async def handle_document_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document uploads"""
    try:
        user_id = str(update.effective_user.id)
        document = update.message.document
        
        logger.info(f"User {user_id} uploaded: {document.file_name}")
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        file_ext = os.path.splitext(document.file_name)[1].lower()
        
        response = f"""📄 <b>تم استلام الملف</b>

<b>الاسم:</b> <code>{document.file_name}</code>
<b>الحجم:</b> {document.file_size // 1024} KB
<b>النوع:</b> {file_ext.upper()}

━━━━━━━━━━━━━━━━━━━━

"""
        
        if file_ext == '.pdf':
            response += "📑 جاري تحليل ملف PDF..."
            # Download and process
            file = await context.bot.get_file(document.file_id)
            file_bytes = await file.download_as_bytearray()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tf:
                tf.write(file_bytes)
                temp_path = tf.name
            
            if ToolRegistry:
                tool = ToolRegistry.get_tool("/ask_pdf")
                if tool:
                    result = await tool().execute(temp_path, user_id)
                    response += "\n\n" + result.get("output", "تم المعالجة")
            
            try:
                os.unlink(temp_path)
            except:
                pass
                
        elif file_ext in ['.xlsx', '.xls', '.csv']:
            response += "📊 <i>تحليل Excel قيد التطوير</i>"
        elif file_ext in ['.doc', '.docx']:
            response += "📝 <i>معالجة Word قيد التطوير</i>"
        else:
            response += f"ℹ️ نوع الملف {file_ext} غير مدعوم للتحليل التلقائي."
        
        await safe_reply(update, response, reply_markup=get_main_keyboard())
        
    except Exception as e:
        logger.error(f"Document error: {e}", exc_info=True)
        await safe_reply(update, "❌ خطأ في معالجة الملف.")

# ═══════════════════════════════════════════════════════════════════════════
# 🎙️ VOICE HANDLER
# ═══════════════════════════════════════════════════════════════════════════

async def handle_voice_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice notes"""
    try:
        user_id = str(update.effective_user.id)
        voice = update.message.voice
        
        logger.info(f"User {user_id} sent voice ({voice.duration}s)")
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await update.message.reply_text("🎙️ <b>جاري تفريغ الصوت...</b>", parse_mode="HTML")
        
        # Download
        file = await context.bot.get_file(voice.file_id)
        file_bytes = await file.download_as_bytearray()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tf:
            tf.write(file_bytes)
            temp_path = tf.name
        
        response = ""
        
        if ToolRegistry:
            tool = ToolRegistry.get_tool("/voice_note")
            if tool:
                result = await tool().execute(temp_path, user_id)
                response = result.get("output", "تم المعالجة")
        
        if not response and llm_client:
            try:
                transcription = await llm_client.transcribe_audio(file_bytes, "audio.ogg")
                response = f"📝 <b>نص التفريغ:</b>\n\n{transcription}"
            except:
                response = "❌ فشل تفريغ الصوت."
        
        if not response:
            response = "⚠️ خدمة التفريغ غير متاحة حالياً."
        
        try:
            os.unlink(temp_path)
        except:
            pass
        
        await safe_reply(update, response, reply_markup=get_main_keyboard())
        
    except Exception as e:
        logger.error(f"Voice error: {e}", exc_info=True)
        await safe_reply(update, "❌ خطأ في معالجة الصوت.")

# ═══════════════════════════════════════════════════════════════════════════
# 🚀 APP SETUP
# ═══════════════════════════════════════════════════════════════════════════

def create_telegram_app():
    """Create and configure Telegram application"""
    try:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            logger.error("TELEGRAM_BOT_TOKEN not set")
            return None
        
        logger.info("Creating Telegram app...")
        app = Application.builder().token(token).build()
        
        # Commands
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("tools", tools_command))
        
        # Media
        app.add_handler(MessageHandler(filters.Document.ALL, handle_document_upload))
        app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice_note))
        
        # Text
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("✅ Telegram app created")
        return app
        
    except Exception as e:
        logger.error(f"Failed to create app: {e}", exc_info=True)
        return None
