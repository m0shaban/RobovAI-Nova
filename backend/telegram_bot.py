"""
🤖 RobovAI Nova - Telegram AI Executive Assistant v2.0
═══════════════════════════════════════════════════════════════
Professional AI Chief of Staff - SaaS Ready Edition
"""

import logging
import os
import re
import random
import tempfile
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

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
        [KeyboardButton("📊 لوحة المعلومات"), KeyboardButton("📁 ملفاتي")],
        [KeyboardButton("⚙️ الإعدادات"), KeyboardButton("ℹ️ عن Nova")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)


def get_tools_keyboard():
    """Tools Sub-Menu - Categorized"""
    keyboard = [
        [KeyboardButton("🎨 إبداعية"), KeyboardButton("💼 أعمال")],
        [KeyboardButton("🔧 تقنية"), KeyboardButton("🌐 ويب")],
        [KeyboardButton("🎭 ترفيه"), KeyboardButton("◀️ القائمة الرئيسية")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_creative_tools_keyboard():
    """Creative Tools"""
    keyboard = [
        [KeyboardButton("/generate_image 🎨"), KeyboardButton("/qr 📱")],
        [KeyboardButton("/chart 📊"), KeyboardButton("/diagram 📐")],
        [KeyboardButton("◀️ الأدوات")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_business_tools_keyboard():
    """Business Tools"""
    keyboard = [
        [KeyboardButton("/ask_pdf 📄"), KeyboardButton("/excel 📊")],
        [KeyboardButton("/currency 💱"), KeyboardButton("/stock 📈")],
        [KeyboardButton("◀️ الأدوات")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_dev_tools_keyboard():
    """Developer Tools"""
    keyboard = [
        [KeyboardButton("/code_fix 🔧"), KeyboardButton("/sql 🗄️")],
        [KeyboardButton("/regex 🔤"), KeyboardButton("/json 📋")],
        [KeyboardButton("◀️ الأدوات")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_web_tools_keyboard():
    """Web & Data Tools"""
    keyboard = [
        [KeyboardButton("/search 🔍"), KeyboardButton("/weather 🌤️")],
        [KeyboardButton("/wikipedia 📚"), KeyboardButton("/translate 🌐")],
        [KeyboardButton("◀️ الأدوات")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_fun_tools_keyboard():
    """Fun & Entertainment Tools"""
    keyboard = [
        [KeyboardButton("/joke 😂"), KeyboardButton("/quote 💭")],
        [KeyboardButton("/cat 🐱"), KeyboardButton("/dog 🐕")],
        [KeyboardButton("/fact 💡"), KeyboardButton("◀️ الأدوات")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# ═══════════════════════════════════════════════════════════════════════════
# 🛡️ SAFE REPLY WRAPPER
# ═══════════════════════════════════════════════════════════════════════════


async def safe_reply(update: Update, text: str, reply_markup=None, parse_mode="HTML"):
    """Robust reply with automatic fallback"""
    try:
        await update.message.reply_text(
            text, reply_markup=reply_markup, parse_mode=parse_mode
        )
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
    """Professional Welcome Screen with verification buttons"""
    logger.info(f"User {update.effective_user.id} started the bot")

    user_name = update.effective_user.first_name or "مستخدم"

    welcome_msg = f"""✨ <b>مرحباً {user_name} في RobovAI Nova</b>

مساعدك التنفيذي الذكي المصمم للأعمال والإنتاجية.

━━━━━━━━━━━━━━━━━━━━

📊 <b>ما يمكنني فعله:</b>

• تحليل المستندات والبيانات
• إنشاء تقارير ورسوم بيانية
• البحث وجمع المعلومات
• معالجة الصوت والصور

━━━━━━━━━━━━━━━━━━━━

🔐 <b>لتفعيل حسابك:</b> اضغط الزر بالأسفل 👇
"""
    # Inline buttons for quick actions
    inline_kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔐 تفعيل الحساب بالإيميل", callback_data="verify_email"),
            InlineKeyboardButton("📱 تفعيل برقم الهاتف", callback_data="verify_phone"),
        ],
        [
            InlineKeyboardButton("🛠️ الأدوات", callback_data="show_tools"),
            InlineKeyboardButton("ℹ️ مساعدة", callback_data="show_help"),
        ],
    ])

    # Try to send logo if exists
    try:
        logo_path = os.path.join("public", "assets", "logo.png")
        if os.path.exists(logo_path):
            await update.message.reply_photo(photo=open(logo_path, "rb"))
    except:
        pass

    await safe_reply(update, welcome_msg, reply_markup=get_main_keyboard())
    # Send inline buttons as a separate message so they don't interfere with ReplyKeyboard
    await update.message.reply_text(
        "⚡ <b>إجراءات سريعة:</b>",
        parse_mode="HTML",
        reply_markup=inline_kb,
    )


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

        # Check if user is in a verify flow first
        if await handle_verify_flow(update, context):
            return

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

        elif message == "📊 لوحة المعلومات":
            # Get tools count
            tools_count = 0
            if ToolRegistry:
                try:
                    registry = ToolRegistry()
                    tools_count = len(registry.tools)
                except:
                    tools_count = 100
            else:
                tools_count = 100

            response = f"""📊 <b>لوحة المعلومات</b>

━━━━━━━━━━━━━━━━━━━━

👤 <b>معلوماتك:</b>
• المعرف: <code>{user_id}</code>
• المنصة: Telegram
• الحالة: نشط ✅

━━━━━━━━━━━━━━━━━━━━

🛠️ <b>إحصائيات النظام:</b>
• الأدوات المتاحة: {tools_count}+
• المنصات المتصلة: 5
• حالة الخدمة: 🟢 متصل

━━━━━━━━━━━━━━━━━━━━

⚡ <b>إجراءات سريعة:</b>
• /tools - قائمة الأدوات
• /help - المساعدة
• /generate_image - توليد صورة"""

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
            web_url = (
                os.getenv("EXTERNAL_URL")
                or os.getenv("RENDER_EXTERNAL_URL")
                or "https://robovai.com"
            )
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
            command = (
                parts[0].split("_")[0] if "_" in parts[0] else parts[0]
            )  # Handle button format
            command = command.replace(" ", "").split()[0]  # Clean command
            arg = parts[1] if len(parts) > 1 else ""

            tool_class = ToolRegistry.get_tool(command)
            if tool_class:
                logger.info(f"Executing tool: {command}")
                try:
                    await context.bot.send_chat_action(
                        chat_id=update.effective_chat.id, action="typing"
                    )
                    tool = tool_class()
                    result = await tool.execute(arg, user_id)

                    # Handle Image Generation Special Case
                    if result.get("image_url"):
                        try:
                            caption = result.get("caption", result.get("output", ""))
                            # Remove markdown image link if present in caption
                            import re

                            caption = re.sub(r"!\[.*?\]\(.*?\)", "", caption).strip()

                            await context.bot.send_chat_action(
                                chat_id=update.effective_chat.id, action="upload_photo"
                            )
                            await context.bot.send_photo(
                                chat_id=update.effective_chat.id,
                                photo=result["image_url"],
                                caption=caption,
                                parse_mode="Markdown",
                            )
                            response = ""  # Handled
                        except Exception as e:
                            logger.error(f"Failed to send photo: {e}")
                            response = result.get("output", "✅ تم التنفيذ")
                    else:
                        response = result.get("output", "✅ تم التنفيذ")

                    logger.info(f"Tool {command} success")
                except Exception as e:
                    logger.error(f"Tool error: {e}", exc_info=True)
                    response = f"❌ خطأ في تنفيذ الأداة: {str(e)[:100]}"
            else:
                response = (
                    f"⚠️ الأمر <code>{command}</code> غير متاح.\nاستخدم /help للمساعدة."
                )

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
                await context.bot.send_chat_action(
                    chat_id=update.effective_chat.id, action="typing"
                )
                if llm_client:
                    response = await llm_client.generate(
                        message, provider="auto", system_prompt=system_prompt
                    )
                else:
                    response = "⚠️ النظام غير متاح حالياً. يرجى المحاولة لاحقاً."
            except Exception as e:
                logger.error(f"LLM error: {e}", exc_info=True)
                response = "⚠️ حدث خطأ. يرجى المحاولة مرة أخرى."

        # Send response
        if response:
            # Check if there is an image URL in the response (from image_gen tool usually handles this internally,
            # but if we want generic handling):
            # Actually, image_gen tool returns a dict. We need to handle the dict result up there.

            # Let's fix the tool execution block instead.
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

        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, action="typing"
        )

        file_ext = os.path.splitext(document.file_name)[1].lower()

        response = f"""📄 <b>تم استلام الملف</b>

<b>الاسم:</b> <code>{document.file_name}</code>
<b>الحجم:</b> {document.file_size // 1024} KB
<b>النوع:</b> {file_ext.upper()}

━━━━━━━━━━━━━━━━━━━━

"""

        if file_ext == ".pdf":
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

        elif file_ext in [".xlsx", ".xls", ".csv"]:
            response += "📊 <i>تحليل Excel قيد التطوير</i>"
        elif file_ext in [".doc", ".docx"]:
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

        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, action="typing"
        )
        await update.message.reply_text(
            "🎙️ <b>جاري تفريغ الصوت...</b>", parse_mode="HTML"
        )

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
                transcription = await llm_client.transcribe_audio(
                    file_bytes, "audio.ogg"
                )
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
# 🔐 TELEGRAM ACCOUNT VERIFICATION (Inline Buttons + Phone)
# ═══════════════════════════════════════════════════════════════════════════

VERIFY_STATE = (
    {}
)  # chat_id -> {"step": ..., "method": "email"|"phone", "email": ..., "user_id": ..., "otp": ...}


def _verify_method_keyboard():
    """Inline keyboard to choose verification method"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📧 بالإيميل", callback_data="verify_email")],
        [InlineKeyboardButton("📱 برقم الهاتف", callback_data="verify_phone")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="verify_cancel")],
    ])


def _verify_cancel_keyboard():
    """Cancel button during verification"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ إلغاء التفعيل", callback_data="verify_cancel")],
    ])


def _verify_confirm_keyboard(otp: str):
    """Inline keyboard with the OTP as a button + confirm + cancel"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📋 نسخ الكود: {otp}", callback_data=f"copy_otp_{otp}")],
        [InlineKeyboardButton(f"✅ تأكيد الكود ({otp})", callback_data=f"confirm_otp_{otp}")],
        [InlineKeyboardButton("🔄 إعادة إرسال كود جديد", callback_data="resend_otp")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="verify_cancel")],
    ])


def _phone_share_keyboard():
    """Reply keyboard requesting phone number share"""
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📱 مشاركة رقم الهاتف", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the account verification flow — show method chooser"""
    chat_id = str(update.effective_chat.id)
    logger.info(f"User {chat_id} started /verify")

    msg = """🔐 <b>تفعيل حساب RobovAI Nova</b>

━━━━━━━━━━━━━━━━━━━━

اختر طريقة التفعيل:

📧 <b>بالإيميل</b> — أدخل البريد الإلكتروني واحصل على كود
📱 <b>برقم الهاتف</b> — شارك رقمك ونبحث عن حسابك

اضغط الزر المناسب 👇"""

    await safe_reply(update, msg, reply_markup=_verify_method_keyboard())


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all inline button callbacks"""
    query = update.callback_query
    await query.answer()

    chat_id = str(query.message.chat_id)
    data = query.data

    # ─── Verification Method Selection ───
    if data == "verify_email":
        VERIFY_STATE[chat_id] = {"step": "awaiting_email", "method": "email"}
        await query.message.reply_text(
            "📧 <b>أدخل البريد الإلكتروني</b> الذي سجلت به في الموقع:\n\n"
            "<i>مثال: user@example.com</i>",
            parse_mode="HTML",
            reply_markup=_verify_cancel_keyboard(),
        )

    elif data == "verify_phone":
        VERIFY_STATE[chat_id] = {"step": "awaiting_phone", "method": "phone"}
        await query.message.reply_text(
            "📱 <b>مشاركة رقم الهاتف</b>\n\n"
            "اضغط الزر بالأسفل لمشاركة رقمك تلقائياً 👇\n\n"
            "<i>أو اكتب بريدك الإلكتروني بدلاً من ذلك</i>",
            parse_mode="HTML",
            reply_markup=_phone_share_keyboard(),
        )

    elif data == "verify_cancel":
        VERIFY_STATE.pop(chat_id, None)
        await query.message.reply_text(
            "❌ تم إلغاء عملية التفعيل.",
            reply_markup=get_main_keyboard(),
        )

    elif data.startswith("confirm_otp_"):
        # User pressed the confirm button — auto-verify
        otp_code = data.replace("confirm_otp_", "")
        state = VERIFY_STATE.get(chat_id)
        if state and state.get("step") == "awaiting_otp" and state.get("otp") == otp_code:
            await _do_verify_otp(query.message, chat_id, state, otp_code)
        else:
            await query.message.reply_text(
                "⚠️ الكود غير صالح أو انتهت الجلسة. أعد المحاولة بـ /verify",
                reply_markup=get_main_keyboard(),
            )

    elif data.startswith("copy_otp_"):
        # Telegram can't copy to clipboard — just show the code clearly
        otp_code = data.replace("copy_otp_", "")
        await query.message.reply_text(
            f"🔑 <b>كود التحقق:</b>\n\n<code>{otp_code}</code>\n\n"
            "📋 اضغط على الكود لنسخه ← أدخله في الموقع",
            parse_mode="HTML",
        )

    elif data == "resend_otp":
        state = VERIFY_STATE.get(chat_id)
        if state and state.get("user_id"):
            await _generate_and_send_otp(query.message, chat_id, state)
        else:
            await query.message.reply_text(
                "⚠️ الجلسة انتهت. ابدأ من جديد بـ /verify",
                reply_markup=get_main_keyboard(),
            )

    # ─── General quick action callbacks ───
    elif data == "show_tools":
        tools_text = """🛠️ <b>اختر فئة الأدوات</b>

🎨 إبداعية | 💼 أعمال | 🔧 تقنية | 🌐 ويب | 🎭 ترفيه

استخدم الأزرار بالأسفل 👇"""
        await query.message.reply_text(tools_text, parse_mode="HTML", reply_markup=get_tools_keyboard())

    elif data == "show_help":
        help_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔐 تفعيل الحساب", callback_data="verify_email")],
            [InlineKeyboardButton("🛠️ الأدوات", callback_data="show_tools")],
        ])
        await query.message.reply_text(
            "📖 <b>المساعدة السريعة</b>\n\n"
            "• /start - القائمة الرئيسية\n"
            "• /verify - تفعيل الحساب\n"
            "• /tools - قائمة الأدوات\n"
            "• /help - المساعدة الكاملة\n\n"
            "💬 أو اكتب أي سؤال وسأجيبك!",
            parse_mode="HTML",
            reply_markup=help_kb,
        )


async def _generate_and_send_otp(message, chat_id: str, state: dict):
    """Generate a new OTP, store it, and send inline buttons"""
    try:
        from backend.core.database import db_client

        otp = str(random.randint(100000, 999999))
        await db_client.store_otp(state["user_id"], otp, "telegram_verify", minutes=10)

        state["otp"] = otp
        state["step"] = "awaiting_otp"
        VERIFY_STATE[chat_id] = state

        email = state.get("email", "")
        msg = f"""✅ <b>تم العثور على الحساب!</b>

📧 <b>البريد:</b> {email}

━━━━━━━━━━━━━━━━━━━━

🔑 <b>كود التحقق:</b>

<code>{otp}</code>

━━━━━━━━━━━━━━━━━━━━

⏱️ صلاحية الكود: <b>10 دقائق</b>

👇 اضغط <b>تأكيد الكود</b> للتفعيل الفوري، أو انسخ الكود وأدخله في الموقع:"""

        await message.reply_text(
            msg,
            parse_mode="HTML",
            reply_markup=_verify_confirm_keyboard(otp),
        )
    except Exception as e:
        logger.error(f"OTP generation error: {e}", exc_info=True)
        await message.reply_text("❌ حدث خطأ تقني. حاول مرة أخرى.")
        VERIFY_STATE.pop(chat_id, None)


async def _do_verify_otp(message, chat_id: str, state: dict, code: str):
    """Verify OTP and activate account"""
    try:
        from backend.core.database import db_client

        valid = await db_client.verify_otp(state["user_id"], code, "telegram_verify")

        if valid:
            await db_client.set_user_verified(state["user_id"], telegram_chat_id=chat_id)
            VERIFY_STATE.pop(chat_id, None)

            msg = """🎉 <b>تم تفعيل حسابك بنجاح!</b>

━━━━━━━━━━━━━━━━━━━━

✅ حسابك مُفعّل الآن ويمكنك الاستمتاع بجميع خدمات RobovAI Nova.

🌐 سجّل دخولك الآن من الموقع وابدأ!

━━━━━━━━━━━━━━━━━━━━

💡 <b>نصيحة:</b> جرّب /tools لاكتشاف كل الأدوات المتاحة!"""

            await message.reply_text(msg, parse_mode="HTML", reply_markup=get_main_keyboard())
        else:
            await message.reply_text(
                "❌ الكود غير صحيح أو منتهي الصلاحية.\n\nاضغط /verify للمحاولة من جديد.",
                reply_markup=get_main_keyboard(),
            )
            VERIFY_STATE.pop(chat_id, None)

    except Exception as e:
        logger.error(f"Verify OTP error: {e}", exc_info=True)
        await message.reply_text("❌ حدث خطأ تقني.")
        VERIFY_STATE.pop(chat_id, None)


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle shared phone number for phone-based verification"""
    chat_id = str(update.effective_chat.id)
    state = VERIFY_STATE.get(chat_id)

    if not state or state.get("method") != "phone":
        return  # Not in phone verify flow

    contact = update.message.contact
    phone = contact.phone_number if contact else None

    if not phone:
        await safe_reply(update, "⚠️ لم أتلق رقم الهاتف. حاول مرة أخرى.")
        return

    # Normalize phone: remove spaces, dashes; keep +
    phone = re.sub(r"[\s\-()]", "", phone)
    if not phone.startswith("+"):
        phone = "+" + phone

    logger.info(f"Phone verification for chat {chat_id}: {phone}")

    try:
        from backend.core.database import db_client

        # Search by Telegram user_id first (if they already linked once)
        # Then search all users — match by phone or by telegram_chat_id
        user = await db_client.get_user_by_telegram_or_phone(chat_id, phone)

        if not user:
            await safe_reply(
                update,
                f"❌ لم يتم العثور على حساب مرتبط بهذا الرقم.\n\n"
                f"📱 الرقم: <code>{phone}</code>\n\n"
                "سجّل أولاً من الموقع ثم عد هنا للتفعيل.\n"
                "أو جرّب التفعيل بالإيميل 👇",
                reply_markup=_verify_method_keyboard(),
            )
            VERIFY_STATE.pop(chat_id, None)
            return

        if user.get("is_verified"):
            await safe_reply(
                update,
                "✅ هذا الحساب مُفعّل بالفعل! يمكنك تسجيل الدخول من الموقع.",
                reply_markup=get_main_keyboard(),
            )
            VERIFY_STATE.pop(chat_id, None)
            return

        # Found unverified account → generate OTP
        state["user_id"] = user["id"]
        state["email"] = user.get("email", "")
        state["phone"] = phone
        VERIFY_STATE[chat_id] = state

        await _generate_and_send_otp(update.message, chat_id, state)

    except AttributeError:
        # get_user_by_telegram_or_phone doesn't exist yet — fall back
        await safe_reply(
            update,
            "⚠️ البحث برقم الهاتف غير متاح حالياً.\n\nجرّب التفعيل بالإيميل 👇",
            reply_markup=_verify_method_keyboard(),
        )
        VERIFY_STATE.pop(chat_id, None)
    except Exception as e:
        logger.error(f"Phone verify error: {e}", exc_info=True)
        await safe_reply(update, "❌ حدث خطأ تقني. حاول مرة أخرى.")
        VERIFY_STATE.pop(chat_id, None)


async def handle_verify_flow(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> bool:
    """Handle verification conversation flow (text-based). Returns True if handled."""
    chat_id = str(update.effective_chat.id)
    state = VERIFY_STATE.get(chat_id)

    if not state:
        return False

    message = (update.message.text or "").strip()

    # Cancel
    if message in ("الغاء", "إلغاء", "/cancel", "cancel"):
        VERIFY_STATE.pop(chat_id, None)
        await safe_reply(
            update, "❌ تم إلغاء عملية التفعيل.", reply_markup=get_main_keyboard()
        )
        return True

    # Step 1: User sent their email
    if state["step"] == "awaiting_email":
        email = message.lower()
        if "@" not in email or "." not in email:
            await safe_reply(
                update,
                "⚠️ هذا لا يبدو بريداً إلكترونياً صحيحاً. حاول مرة أخرى:",
                reply_markup=_verify_cancel_keyboard(),
            )
            return True

        try:
            from backend.core.database import db_client

            user = await db_client.get_user_by_email_unverified(email)

            if not user:
                await safe_reply(
                    update,
                    "❌ لم يتم العثور على حساب بهذا البريد.\n\nسجّل أولاً من الموقع ثم عد هنا للتفعيل.",
                    reply_markup=_verify_method_keyboard(),
                )
                VERIFY_STATE.pop(chat_id, None)
                return True

            if user.get("is_verified"):
                await safe_reply(
                    update,
                    "✅ هذا الحساب مُفعّل بالفعل! يمكنك تسجيل الدخول من الموقع.",
                    reply_markup=get_main_keyboard(),
                )
                VERIFY_STATE.pop(chat_id, None)
                return True

            # Found unverified account → generate OTP with inline buttons
            state["user_id"] = user["id"]
            state["email"] = email
            VERIFY_STATE[chat_id] = state

            await _generate_and_send_otp(update.message, chat_id, state)
            return True

        except Exception as e:
            logger.error(f"Verify email error: {e}", exc_info=True)
            await safe_reply(update, "❌ حدث خطأ تقني. حاول مرة أخرى.")
            VERIFY_STATE.pop(chat_id, None)
            return True

    # Step: User typed email while in phone flow (fallback)
    if state["step"] == "awaiting_phone":
        email = message.lower()
        if "@" in email and "." in email:
            # Switch to email flow
            state["step"] = "awaiting_email"
            state["method"] = "email"
            VERIFY_STATE[chat_id] = state
            return await handle_verify_flow(update, context)
        # Not an email, not a phone share — ignore
        await safe_reply(
            update,
            "📱 اضغط زر <b>مشاركة رقم الهاتف</b> بالأسفل، أو اكتب بريدك الإلكتروني.",
            reply_markup=_phone_share_keyboard(),
        )
        return True

    # Step 2: User entered OTP manually
    if state["step"] == "awaiting_otp":
        code = message.strip()

        if not code.isdigit() or len(code) != 6:
            await safe_reply(
                update,
                "⚠️ الكود يتكون من 6 أرقام. حاول مرة أخرى أو اضغط إلغاء.",
                reply_markup=_verify_cancel_keyboard(),
            )
            return True

        await _do_verify_otp(update.message, chat_id, state, code)
        return True

    return False


# ═══════════════════════════════════════════════════════════════════════════
# �🚀 APP SETUP
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
        app.add_handler(CommandHandler("verify", verify_command))

        # Inline button callbacks (verify, tools, help, etc.)
        app.add_handler(CallbackQueryHandler(handle_callback_query))

        # Phone contact sharing (for phone verification)
        app.add_handler(MessageHandler(filters.CONTACT, handle_contact))

        # Media
        app.add_handler(MessageHandler(filters.Document.ALL, handle_document_upload))
        app.add_handler(
            MessageHandler(filters.VOICE | filters.AUDIO, handle_voice_note)
        )

        # Text
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        logger.info("✅ Telegram app created")
        return app

    except Exception as e:
        logger.error(f"Failed to create app: {e}", exc_info=True)
        return None
