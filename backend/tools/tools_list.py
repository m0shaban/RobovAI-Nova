"""
قائمة شاملة بجميع أدوات RobovAI الـ 66
"""

ALL_TOOLS = [
    # 🎉 Fun & Viral (10 tools)
    {"name": "/roast", "desc": "Roast مضحك", "category": "fun", "premium": False},
    {"name": "/rizz", "desc": "ردود Rizz", "category": "fun", "premium": False},
    {"name": "/dream", "desc": "تفسير أحلام", "category": "fun", "premium": False},
    {"name": "/horoscope", "desc": "الأبراج", "category": "fun", "premium": False},
    {"name": "/fight", "desc": "معركة خيالية", "category": "fun", "premium": False},
    {"name": "/joke", "desc": "نكتة عشوائية", "category": "fun", "premium": False},
    {"name": "/cat", "desc": "صورة قطة", "category": "fun", "premium": False},
    {"name": "/dog", "desc": "صورة كلب", "category": "fun", "premium": False},
    {"name": "/bored", "desc": "نشاط عشوائي", "category": "fun", "premium": False},
    {"name": "/trivia", "desc": "سؤال ثقافي", "category": "fun", "premium": False},
    
    # 🛠️ Utility (10 tools)
    {"name": "/ip", "desc": "معلومات IP", "category": "utility", "premium": False},
    {"name": "/crypto", "desc": "أسعار العملات", "category": "utility", "premium": False},
    {"name": "/shorten", "desc": "اختصار رابط", "category": "utility", "premium": False},
    {"name": "/password", "desc": "كلمة سر قوية", "category": "utility", "premium": False},
    {"name": "/uuid", "desc": "UUID عشوائي", "category": "utility", "premium": False},
    {"name": "/qr", "desc": "QR Code", "category": "utility", "premium": False},
    {"name": "/website_status", "desc": "حالة موقع", "category": "utility", "premium": False},
    {"name": "/currency", "desc": "تحويل عملات", "category": "utility", "premium": False},
    {"name": "/color", "desc": "ألوان عشوائية", "category": "utility", "premium": False},
    {"name": "/unit", "desc": "تحويل وحدات", "category": "utility", "premium": False},
    
    # 💻 Developer (10 tools)
    {"name": "/code_fix", "desc": "إصلاح أكواد", "category": "dev", "premium": True},
    {"name": "/sql", "desc": "SQL Generator", "category": "dev", "premium": True},
    {"name": "/regex", "desc": "Regex Helper", "category": "dev", "premium": False},
    {"name": "/explain_code", "desc": "شرح كود", "category": "dev", "premium": True},
    {"name": "/arduino", "desc": "كود Arduino", "category": "dev", "premium": False},
    {"name": "/timestamp", "desc": "وقت Unix", "category": "dev", "premium": False},
    {"name": "/hash", "desc": "Hash نص", "category": "dev", "premium": False},
    {"name": "/lorem", "desc": "Lorem Ipsum", "category": "dev", "premium": False},
    {"name": "/json_format", "desc": "تنسيق JSON", "category": "dev", "premium": False},
    {"name": "/base64", "desc": "Base64", "category": "dev", "premium": False},
    
    # 🌍 Life & Info (10 tools)
    {"name": "/weather", "desc": "الطقس", "category": "life", "premium": False},
    {"name": "/wiki", "desc": "ويكيبيديا", "category": "life", "premium": False},
    {"name": "/definition", "desc": "التعريف", "category": "life", "premium": False},
    {"name": "/number_fact", "desc": "حقيقة عن رقم", "category": "life", "premium": False},
    {"name": "/holiday", "desc": "العطلات", "category": "life", "premium": False},
    {"name": "/travel_plan", "desc": "خطة سفر", "category": "life", "premium": True},
    {"name": "/meal_plan", "desc": "خطة وجبات", "category": "life", "premium": True},
    {"name": "/workout", "desc": "برنامج تمارين", "category": "life", "premium": True},
    {"name": "/gift", "desc": "اقتراح هدية", "category": "life", "premium": False},
    {"name": "/movie_rec", "desc": "اقتراح فيلم", "category": "life", "premium": False},
    
    # 📚 Content & Education (10 tools)
    {"name": "/social", "desc": "منشور سوشيال", "category": "content", "premium": True},
    {"name": "/script", "desc": "سكريبت فيديو", "category": "content", "premium": True},
    {"name": "/email_formal", "desc": "إيميل رسمي", "category": "content", "premium": False},
    {"name": "/email_angry", "desc": "إيميل غاضب", "category": "content", "premium": False},
    {"name": "/eli5", "desc": "اشرحلي كطفل", "category": "content", "premium": False},
    {"name": "/quiz", "desc": "كويز", "category": "content", "premium": False},
    {"name": "/book_rec", "desc": "اقتراح كتاب", "category": "content", "premium": False},
    {"name": "/translate_egy", "desc": "ترجمة مصرية", "category": "content", "premium": False},
    {"name": "/grammar", "desc": "تصحيح لغوي", "category": "content", "premium": False},
    {"name": "/synonym", "desc": "مرادفات", "category": "content", "premium": False},
    
    # 👁️ Vision & Documents (6 tools - NEW)
    {"name": "/scan_receipt", "desc": "مسح فاتورة", "category": "vision", "premium": True},
    {"name": "/analyze_id", "desc": "قراءة بطاقة", "category": "vision", "premium": True},
    {"name": "/chart_insights", "desc": "تحليل رسم بياني", "category": "vision", "premium": False},
    {"name": "/ask_pdf", "desc": "تحليل PDF", "category": "vision", "premium": True},
    {"name": "/video_summary", "desc": "تلخيص فيديو", "category": "vision", "premium": True},
    {"name": "/meme_explain", "desc": "شرح ميم", "category": "vision", "premium": False},
    
    # 🎤 Voice & Audio (4 tools - NEW)
    {"name": "/voice_note", "desc": "Voice Note", "category": "audio", "premium": True},
    {"name": "/tts_custom", "desc": "Text-to-Speech", "category": "audio", "premium": True},
    {"name": "/clean_audio", "desc": "تحسين صوت", "category": "audio", "premium": False},
    {"name": "/meeting_notes", "desc": "محضر اجتماع", "category": "audio", "premium": True},
    
    # 🛡️ Safety & Business (6 tools - NEW)
    {"name": "/check_content", "desc": "فحص محتوى", "category": "safety", "premium": False},
    {"name": "/legal_summary", "desc": "تلخيص قانوني", "category": "safety", "premium": True},
    {"name": "/outfit_rate", "desc": "تقييم ملابس", "category": "safety", "premium": False},
    {"name": "/dish_recipe", "desc": "وصفة من صورة", "category": "safety", "premium": False},
    {"name": "/compare_offers", "desc": "مقارنة أسعار", "category": "safety", "premium": True},
    {"name": "/translate_voice", "desc": "ترجمة صوتية", "category": "safety", "premium": True},
]

# تصنيف الأدوات حسب الفئة
def get_tools_by_category():
    categories = {
        "fun": {"icon": "🎉", "title": "Fun & Viral", "tools": []},
        "utility": {"icon": "🛠️", "title": "Utility Belt", "tools": []},
        "dev": {"icon": "💻", "title": "Developer", "tools": []},
        "life": {"icon": "🌍", "title": "Life & Info", "tools": []},
        "content": {"icon": "📚", "title": "Content & Edu", "tools": []},
        "vision": {"icon": "👁️", "title": "Vision (جديد)", "tools": []},
        "audio": {"icon": "🎤", "title": "Audio (جديد)", "tools": []},
        "safety": {"icon": "🛡️", "title": "Safety & Business (جديد)", "tools": []},
    }
    
    for tool in ALL_TOOLS:
        cat = tool["category"]
        if cat in categories:
            categories[cat]["tools"].append(tool)
    
    return categories
