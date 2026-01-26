"""
🤖 RobovAI Nova - Telegram AI Chief of Staff
═══════════════════════════════════════════════════════════════
Professional Assistant for Productivity, Business, and Data Analysis.
"""

import logging
import os
import tempfile
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

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
# 📊 STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

USER_EDIT_STATE = {}  # Store user editing preferences

# ═══════════════════════════════════════════════════════════════════════════
# ⌨️ PROFESSIONAL KEYBOARD
# ═══════════════════════════════════════════════════════════════════════════

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

# ═══════════════════════════════════════════════════════════════════════════
# 🛡️ SAFE REPLY WRAPPER
# ═══════════════════════════════════════════════════════════════════════════

async def safe_reply(update: Update, text: str, reply_markup=None, parse_mode="Markdown"):
    """
    Robust Reply Wrapper:
    1. Tries to send with Markdown.
    2. If it fails (400 Bad Request), sends as Plain Text.
    This prevents the bot from crashing on LLM formatting errors.
    """
    try:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        logger.info(f"Successfully sent message to user {update.effective_user.id}")
    except Exception as e:
        logger.warning(f"Markdown Reply Failed: {e}. Falling back to plain text.")
        try:
            # Fallback: Plain text
            await update.message.reply_text(text, reply_markup=reply_markup)
            logger.info(f"Successfully sent plain text message to user {update.effective_user.id}")
        except Exception as e2:
            logger.error(f"Reply Failed Completely: {e2}", exc_info=True)

# ═══════════════════════════════════════════════════════════════════════════
# 🎯 COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════════════════

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Modern Start Screen"""
    logger.info(f"User {update.effective_user.id} started the bot")
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
    logger.info(f"User {update.effective_user.id} requested help")
    help_text = """🆘 **دليل الأوامر السريعة**

🔹 **البحث والمعلومات:**
`/search [سؤالك]` - بحث حي في جوجل/الويب.
`/weather [المدينة]` - معلومات الطقس.
`/crypto [رمز]` - أسعار العملات الرقمية.

🔹 **الوسائط والملفات:**
`/qr [نص أو رابط]` - إنشاء كود QR.
`/password` - توليد كلمة مرور قوية.

🔹 **الترفيه:**
`/joke` - نكتة عشوائية.
`/cat` - صورة قطة.
`/dog` - صورة كلب.

💡 *نصيحة: يمكنك دائماً التحدث معي باللغة الطبيعية!*
"""
    await safe_reply(update, help_text)

async def tools_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show available tools"""
    logger.info(f"User {update.effective_user.id} requested tools list")
    await safe_reply(update, "🛠️ انتقلت الأدوات إلى قائمة **إجراءات سريعة** في القائمة الرئيسية.", reply_markup=get_main_keyboard())

# ═══════════════════════════════════════════════════════════════════════════
# 📨 MESSAGE HANDLER
# ═══════════════════════════════════════════════════════════════════════════

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Core Logic for 'AI Chief of Staff' - Modern & Professional.
    """
    try:
        user_id = str(update.effective_user.id)
        message = update.message.text or ""
        
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
2️⃣ **معلومات طقس**: `/weather Cairo`
3️⃣ **كلمة مرور**: `/password`
4️⃣ **QR Code**: `/qr نص أو رابط`
"""
        
        elif message == "📂 ملفاتي وتحليلاتي":
            response = """📂 **مركز المستندات والبيانات**
            
يمكنك إرسال الملفات التالية وسأقوم بتحليلها فوراً:
📄 **PDF/Word**: تلخيص واستخراج النقاط الهامة.
📊 **Excel/CSV**: تحليل مالي وإحصائي شامل.
🖼️ **صور**: استخراج نص (OCR) أو تحليل.
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
            web_url = os.getenv("EXTERNAL_URL") or os.getenv("RENDER_EXTERNAL_URL") or "https://robovai.com"
            response = f"""🌐 **منصة RobovAI Nova المتكاملة**

للوصول إلى لوحات المعلومات المتقدمة (Dashboards)، إدارة المشاريع، والتقارير التفصيلية، يرجى زيارة بوابتك الشخصية:

🔗 {web_url}

💡 *هنا في تليجرام نركز على السرعة، وهناك نركز على العمق.*"""
        
        elif message == "🆘 مساعدة / أوامر":
            await help_command(update, context)
            return
        
        # ════════════════════════════════════════════════════════════════════════
        # 2. TOOL COMMANDS (Using ToolRegistry)
        # ════════════════════════════════════════════════════════════════════════
        elif message.startswith("/") and ToolRegistry:
            parts = message.split(" ", 1)
            command = parts[0]
            arg = parts[1] if len(parts) > 1 else ""
            
            tool_class = ToolRegistry.get_tool(command)
            if tool_class:
                logger.info(f"Executing tool: {command} for user {user_id}")
                try:
                    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
                    tool_instance = tool_class()
                    result = await tool_instance.execute(arg, user_id)
                    response = result.get("output", "تم التنفيذ ✅")
                    logger.info(f"Tool {command} executed successfully for user {user_id}")
                except Exception as e:
                    logger.error(f"Tool execution error for {command}: {e}", exc_info=True)
                    response = f"❌ حدث خطأ أثناء تنفيذ الأداة: {str(e)}"
            else:
                logger.warning(f"Unknown command: {command}")
                response = f"⚠️ الأمر غير معروف: {command}\nاستخدم /help لعرض الأوامر المتاحة."
        
        # ════════════════════════════════════════════════════════════════════════
        # 3. AI EXECUTIVE CHAT (MODERN PERSONA)
        # ════════════════════════════════════════════════════════════════════════
        elif not response:
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
                if llm_client:
                    response = await llm_client.generate(message, provider="groq", system_prompt=system_prompt)
                    logger.info(f"LLM response generated for user {user_id}")
                else:
                    response = "⚠️ **عذراً،** النظام الذكي غير متاح حالياً. يرجى المحاولة لاحقاً."
                    logger.error("LLM client not available")
            except Exception as e:
                logger.error(f"LLM Error for user {user_id}: {e}", exc_info=True)
                response = "⚠️ **عذراً،** حدث انقطاع لحظي في الاتصال العصبي. يرجى المحاولة مرة أخرى."
        
        # Send response
        if response:
            await safe_reply(update, response, reply_markup=get_main_keyboard())
        
    except Exception as e:
        logger.error(f"Critical error in handle_message: {e}", exc_info=True)
        try:
            await safe_reply(update, "⚠️ **حدث خطأ تقني.**\nعذراً، لم أتمكن من معالجة طلبك. يرجى المحاولة مرة أخرى.")
        except:
            pass

# ═══════════════════════════════════════════════════════════════════════════
# 📎 DOCUMENT UPLOAD HANDLER
# ═══════════════════════════════════════════════════════════════════════════

async def handle_document_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document uploads (PDF, Excel, Word, etc.)"""
    try:
        user_id = str(update.effective_user.id)
        document = update.message.document
        
        logger.info(f"User {user_id} uploaded document: {document.file_name}")
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Download file
        file = await context.bot.get_file(document.file_id)
        file_bytes = await file.download_as_bytearray()
        
        # Save temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(document.file_name)[1]) as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name
        
        # Try to use appropriate tool based on file type
        file_ext = os.path.splitext(document.file_name)[1].lower()
        response = f"📄 تم استلام الملف: `{document.file_name}`\n\n"
        
        if file_ext == '.pdf' and ToolRegistry:
            tool_class = ToolRegistry.get_tool("/ask_pdf")
            if tool_class:
                tool = tool_class()
                result = await tool.execute(temp_path, user_id)
                response += result.get("output", "تم معالجة الملف")
            else:
                response += "📑 ملف PDF تم استلامه. استخدم `/ask_pdf` مع رابط الملف للتحليل."
        elif file_ext in ['.xlsx', '.xls', '.csv']:
            response += "📊 ملف Excel/CSV تم استلامه. جاري تحليله...\n"
            response += "_(ملاحظة: تحليل البيانات قيد التطوير)_"
        elif file_ext in ['.doc', '.docx']:
            response += "📝 ملف Word تم استلامه.\n_(ملاحظة: معالجة Word قيد التطوير)_"
        else:
            response += "ℹ️ نوع الملف غير مدعوم حالياً للتحليل التلقائي."
        
        # Cleanup
        try:
            os.unlink(temp_path)
        except:
            pass
        
        await safe_reply(update, response, reply_markup=get_main_keyboard())
        
    except Exception as e:
        logger.error(f"Error handling document: {e}", exc_info=True)
        await safe_reply(update, "❌ حدث خطأ أثناء معالجة الملف. يرجى المحاولة مرة أخرى.")

# ═══════════════════════════════════════════════════════════════════════════
# 🎙️ VOICE NOTE HANDLER
# ═══════════════════════════════════════════════════════════════════════════

async def handle_voice_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice note uploads"""
    try:
        user_id = str(update.effective_user.id)
        voice = update.message.voice
        
        logger.info(f"User {user_id} sent voice note (duration: {voice.duration}s)")
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await update.message.reply_text("🎙️ **جاري تفريغ الصوت...**")
        
        # Download voice file
        file = await context.bot.get_file(voice.file_id)
        file_bytes = await file.download_as_bytearray()
        
        # Save temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name
        
        # Try to transcribe using LLM or VoiceNote tool
        response = ""
        
        if ToolRegistry:
            tool_class = ToolRegistry.get_tool("/voice_note")
            if tool_class:
                tool = tool_class()
                result = await tool.execute(temp_path, user_id)
                response = result.get("output", "تم معالجة الصوت")
            else:
                # Fallback to direct LLM transcription
                if llm_client:
                    try:
                        transcription = await llm_client.transcribe_audio(file_bytes, "audio.ogg")
                        response = f"📝 **نص التفريغ:**\n\n{transcription}"
                    except Exception as e:
                        logger.error(f"Transcription error: {e}")
                        response = "❌ فشل تفريغ الصوت. يرجى المحاولة مرة أخرى."
                else:
                    response = "⚠️ خدمة تفريغ الصوت غير متاحة حالياً."
        else:
            response = "⚠️ خدمة تفريغ الصوت غير متاحة حالياً."
        
        # Cleanup
        try:
            os.unlink(temp_path)
        except:
            pass
        
        await safe_reply(update, response, reply_markup=get_main_keyboard())
        
    except Exception as e:
        logger.error(f"Error handling voice note: {e}", exc_info=True)
        await safe_reply(update, "❌ حدث خطأ أثناء معالجة الصوت. يرجى المحاولة مرة أخرى.")

# ═══════════════════════════════════════════════════════════════════════════
# 🚀 APP SETUP
# ═══════════════════════════════════════════════════════════════════════════

def create_telegram_app():
    """Create and configure Telegram application"""
    try:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            logger.error("TELEGRAM_BOT_TOKEN not set in environment")
            return None
        
        logger.info("Creating Telegram application...")
        application = Application.builder().token(token).build()
        
        # Commands
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("tools", tools_command))
        
        # Media Handlers
        application.add_handler(MessageHandler(filters.Document.ALL, handle_document_upload))
        application.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice_note))
        
        # Text Message Handler
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("✅ Telegram application created successfully")
        return application
        
    except Exception as e:
        logger.error(f"Failed to build Telegram App: {e}", exc_info=True)
        return None
