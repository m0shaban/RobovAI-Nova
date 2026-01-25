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

def get_main_keyboard():
    """Return the persistent professional dashboard keyboard"""
    keyboard = [
        [KeyboardButton("📋 ملخص اليوم"), KeyboardButton("📄 تحليل وثيقة")],
        [KeyboardButton("🎙️ تفريغ صوتي"), KeyboardButton("🔎 بحث متقدم")],
        [KeyboardButton("🛠️ أدواتي"), KeyboardButton("❓ مساعدة")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)

# ═══════════════════════════════════════════════════════════════════════════
# 🎯 COMMAND HANDLERS
# ═══════════════════════════════════════════════════════════════════════════

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Executive Welcome Message"""
    user_name = update.effective_user.first_name
    welcome_text = f"""
مرحباً أستاذ **{user_name}**،

أنا **RobovAI Nova**، مساعدك التنفيذي الذكي (AI Chief of Staff).
تم تصميمي خصيصاً لزيادة إنتاجيتك، تنظيم أعمالك، ومساعدتك في اتخاذ القرارات بدقة.

يمكنني مساعدتك في:
🔹 **تحليل المستندات** (PDF, Docs) واستخراج أهم النقاط.
🔹 **تفريغ الملاحظات الصوتية** وتحويلها لمهام عمل.
🔹 **البحث المتقدم** عن معلومات موثوقة.
🔹 **إدارة الأدوات اليومية** (حسابات، عملات، توقيتات).

كيف يمكنني مساعدتك الآن؟
    """
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Professional Usage Guide"""
    help_text = """
📖 **دليل المساعد التنفيذي**

نظامي مصمم للعمل بدقة وكفاءة. إليك كيفية الاستفادة القصوى:

▪️ **إرسال الملفات**: قم بإرسال أي ملف (PDF/Word) وسأقوم بتلخيصه فوراً.
▪️ **الملاحظات الصوتية**: أرسل تسجيل صوتي وسأحوله لنص مكتوب ومنسق.
▪️ **البحث**: استخدم "بحث متقدم" للوصول لمعلومات دقيقة من الويب.
▪️ **الأدوات**: اضغط على "أدواتي" للوصول للآلة الحاسبة، محول العملات، وغيرها.

أنا أفهم اللغة العربية (الفصحى والبيضاء) والإنجليزية بطلاقة.
    """
    await update.message.reply_text(help_text, reply_markup=get_main_keyboard(), parse_mode='Markdown')

async def tools_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List Verified Productivity Tools"""
    text = """
🛠️ **حقيبة الأدوات التنفيذية**

1️⃣ **أدوات الأعمال:**
• `/curr` - متابعة أسعار العملات لحظياً.
• `/email` - التحقق من صحة البريد الإلكتروني.
• `/ocr` - استخراج النصوص من الصور (قريباً).

2️⃣ **المعرفة والبحث:**
• `/wiki` - بحث موسوعي موثوق.
• `/search` - بحث ويب متقدم.

3️⃣ **الأدوات المساعدة:**
• `/calc` - آلة حاسبة متقدمة.
• `/translate` - ترجمة احترافية للوثائق والنصوص.

لأي استفسار معقد، فقط اكتب سؤالك مباشرة.
    """
    await update.message.reply_text(text, parse_mode='Markdown')

# ═══════════════════════════════════════════════════════════════════════════
# 🧩 FEATURE HANDLERS
# ═══════════════════════════════════════════════════════════════════════════

# Additional Imports
try:
    from backend.tools.files import PDFReaderTool, DocxReaderTool
except ImportError:
    PDFReaderTool = None
    DocxReaderTool = None

try:
    from backend.tools.office import ExcelAnalyzerTool, CalendarEventTool
except ImportError:
    ExcelAnalyzerTool = None
    CalendarEventTool = None

async def handle_document_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Professional Document Analysis Handler.
    Automatically detects PDF/Docx/Excel/CSV.
    """
    doc = update.message.document
    file_name = doc.file_name.lower()
    
    await update.message.reply_text(f"⏳ **جاري تحليل الملف:** `{file_name}`...", parse_mode="Markdown")

    # 1. Get File
    new_file = await doc.get_file()
    file_byte_array = await new_file.download_as_bytearray()
    file_bytes = bytes(file_byte_array)

    text_content = ""
    extract_status = "error"

    # 2. Extract Text
    if file_name.endswith('.pdf') and PDFReaderTool:
        tool = PDFReaderTool()
        result = await tool.execute("", "", file_content=file_bytes)
        text_content = result.get('output', '')
        extract_status = result.get('status')
    
    elif (file_name.endswith('.docx') or file_name.endswith('.doc')) and DocxReaderTool:
        tool = DocxReaderTool()
        result = await tool.execute("", "", file_content=file_bytes)
        text_content = result.get('output', '')
        extract_status = result.get('status')

    elif (file_name.endswith('.xlsx') or file_name.endswith('.csv')) and ExcelAnalyzerTool:
        tool = ExcelAnalyzerTool()
        result = await tool.execute("", "", file_content=file_bytes, filename=file_name)
        # For Excel, the output IS the report, no need to summarize further usually
        await update.message.reply_text(result.get('output', 'Error parsing Excel'), parse_mode="Markdown")
        return
    
    else:
        await update.message.reply_text("⚠️ عذراً، هذا النوع من الملفات غير مدعوم حالياً (فقط PDF, Word, Excel, CSV).")
        return

    # 3. Process Result (Summary for Text Docs)
    if extract_status == "success" and text_content:
        # Limit token count roughly
        preview_text = text_content[:4000] 
        
        system_prompt = """
        أنت مساعد تنفيذي خبير. قم بتلخيص هذا المستند بشكل احترافي.
        - ابدأ بـ "📌 **ملخص تنفيذي**"
        - اذكر أهم 3-5 نقاط في شكل قائمة.
        - حدد أي إجراءات مطلوبة (Action Items).
        - اللغة: عربية احترافية.
        """
        
        try:
            summary = await llm_client.generate(
                f"لخص هذا النص:\n{preview_text}",
                provider="groq",
                system_prompt=system_prompt
            )
            await update.message.reply_text(summary, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Summary Generation Error: {e}")
            await update.message.reply_text("✅ تم استخراج النص، لكن حدث خطأ أثناء التلخيص.")
    else:
         await update.message.reply_text(f"❌ فشل استخراج النص: {text_content}")

async def handle_voice_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle Voice Notes with 'Transcription + Action Item' pipeline.
    """
    voice = update.message.voice or update.message.audio
    
    # Check duration
    if voice.duration > 120:
        await update.message.reply_text("⚠️ الملاحظة الصوتية طويلة جداً (أكثر من دقيقتين). يرجى إرسال ملاحظات أقصر حالياً.")
        return

    await update.message.reply_text("🎙️ **جاري المعالجة...** (يتم الآن تحويل الصوت لنص)", parse_mode="Markdown")
    
    response_text = """
    ✅ **تم استلام الملاحظة.**
    (جاري التطوير لربط خدمة Whisper بشكل كامل)
    """
    await update.message.reply_text(response_text, parse_mode="Markdown")

# ═══════════════════════════════════════════════════════════════════════════
# 💬 MESSAGE HANDLER & INTELLIGENT ROUTING
# ═══════════════════════════════════════════════════════════════════════════

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages and menu interaction with professional routing"""
    user_id = str(update.effective_user.id)
    message = update.message.text
    
    logger.info(f"Executive Request from {user_id}: {message}")
    response = ""

    # 1. Main Menu Navigation
    if message == "📋 ملخص اليوم":
        response = "📊 **لوحة المعلومات اليومية**\n\nلا توجد اجتماعات مسجلة اليوم.\nحالة السيرفر: ✅ ممتاز."
    
    elif message == "📄 تحليل وثيقة":
        response = "📎 من فضلك قم **برفع الملف** (PDF, Word, Excel) الآن وسأقوم بتحليله فوراً."
    
    elif message == "🎙️ تفريغ صوتي":
        response = "🎙️ اضغط على زر التسجيل في تيليجرام وأرسل ملاحظتك الصوتية مباشرة."
        
    elif message == "🔎 بحث متقدم":
        response = "🔍 اكتب ما تود البحث عنه بدقة، مثلاً: 'تحليل سوق العقارات في مصر 2025'."
        
    elif message == "🛠️ أدواتي":
        await tools_command(update, context)
        return

    elif message == "❓ مساعدة":
        await help_command(update, context)
        return

    # 2. Command Parsing for New Features
    # Calendar Creation: "جدول اجتماع | 2025-01-01 10:00"
    if message.startswith("جدول") or message.startswith("/schedule"):
        if CalendarEventTool:
             # Strip command keywords "جدول" or "/schedule" approx
             # This is a basic heuristic
             clean_input = message.replace("جدول", "").replace("/schedule", "").strip()
             tool = CalendarEventTool()
             result = await tool.execute(clean_input, user_id)
             
             if result.get("status") == "success":
                 # Send ICS file
                 from telegram import InputFile
                 file_content = result.get("file_content")
                 # We need to write to a temp file or bytesio
                 import io
                 f = io.BytesIO(file_content.encode('utf-8'))
                 f.name = "meeting.ics"
                 await update.message.reply_document(document=f, caption="📅 تم إنشاء ملف الاجتماع.")
                 return # skip sending text response
             else:
                 response = result.get('output')

    # 3. AI Intelligence Layer
    if not response:
        # Strict Professional System Prompt
        system_prompt = """
        أنت (RobovAI Nova)، مساعد تنفيذي محترف (AI Chief of Staff).
        - هويتك: ذكاء اصطناعي متطور، دقيق، وموثوق "سكين سويسري رقمي".
        - الصلاحيات: يمكنك تحليل البيانات (Excel)، إدارة المستندات (PDF)، وإنشاء الجداول.
        - لغتك: عربية "بيضاء" (راقية، واضحة، مهنية).
        - لو طلب المستخدم رسم بياني، اقترح استخدام `/chart`.
        - لو طلب تحويل عملة، اقترح `/convert`.
        """
        
        try:
            if SmartToolRouter:
                routing_result = await SmartToolRouter.route_message(message, user_id, platform="telegram")
                if routing_result['type'] == 'tool':
                    # Allow Chart/Convert logic to flow here if routed
                    tool_name = routing_result.get('tool')
                    if tool_name in ["/joke", "/meme"]:
                         response = "عذراً، أنا أركز على العمل حالياً."
                    else:
                         response = routing_result['result'].get('output', 'تم تنفيذ الأمر.')
                else:
                    response = await llm_client.generate(
                        message,
                        provider="groq",
                        system_prompt=system_prompt
                    )
            else:
                 response = await llm_client.generate(
                        message,
                        provider="groq",
                        system_prompt=system_prompt
                    )
        except Exception as e:
            logger.error(f"Router Error: {e}")
            response = "عذراً، حدث خطأ تقني. يرجى المحاولة لاحقاً."

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
