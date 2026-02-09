"""
HTML Landing Page Generator & Document Creator Tools
"""
from typing import Dict, Any
from .base import BaseTool
from backend.core.llm import llm_client
import os, uuid, re


class LandingPageTool(BaseTool):
    """Generates complete HTML landing pages using AI."""

    @property
    def name(self) -> str:
        return "/landing_page"

    @property
    def description(self) -> str:
        return "Generates a complete, responsive HTML landing page from a description. Returns a downloadable HTML file with modern design."

    @property
    def cost(self) -> int:
        return 3

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"""أنت مطور ويب محترف. أنشئ صفحة HTML كاملة (Landing Page) بناءً على الوصف التالي:

"{user_input}"

المطلوب:
1. صفحة HTML كاملة مع CSS مدمج (لا ملفات خارجية)
2. تصميم modern responsive يعمل على الموبايل و الديسكتوب
3. استخدم gradient backgrounds و modern fonts (Google Fonts)
4. أضف sections: Hero, Features, About, CTA, Footer
5. أضف animations بسيطة بـ CSS
6. اكتب المحتوى بناءً على وصف المستخدم
7. اجعل التصميم جذاب واحترافي
8. أضف meta tags مناسبة للـ SEO

أعطني الكود HTML الكامل فقط بدون أي شرح. ابدأ بـ <!DOCTYPE html> وانتهي بـ </html>."""

        output = await llm_client.generate(prompt, provider="auto", max_tokens=8000)

        # Extract HTML from response
        html_match = re.search(r'(<!DOCTYPE html>[\s\S]*?</html>)', output, re.IGNORECASE)
        if html_match:
            html_content = html_match.group(1)
        else:
            # Try extracting from code blocks
            code_match = re.search(r'```(?:html)?\s*([\s\S]*?)```', output)
            html_content = code_match.group(1).strip() if code_match else output

        # Save the file
        file_id = str(uuid.uuid4())[:8]
        filename = f"landing_{file_id}.html"
        upload_dir = os.path.join("uploads", "files")
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        download_url = f"/uploads/files/{filename}"

        return {
            "status": "success",
            "output": f"""✅ **تم إنشاء صفحة الـ Landing Page بنجاح!** 🎨

📄 **الملف:** [{filename}]({download_url})
🔗 **رابط المعاينة:** [{download_url}]({download_url})
📥 **تحميل:** [اضغط هنا للتحميل]({download_url})

📐 **المواصفات:**
- تصميم متجاوب (Responsive)
- Modern CSS مع Animations
- SEO-Ready Meta Tags
- يعمل على جميع الأجهزة

> 💡 يمكنك تعديل الصفحة أو طلب صفحة جديدة بمواصفات مختلفة""",
            "tokens_deducted": self.cost,
            "file_url": download_url,
        }


class EmailComposerTool(BaseTool):
    """Composes professional emails."""

    @property
    def name(self) -> str:
        return "/compose_email"

    @property
    def description(self) -> str:
        return "Composes a professional email in Arabic or English with proper formatting, subject line, and structure."

    @property
    def cost(self) -> int:
        return 1

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"""أنت خبير في كتابة الإيميلات الاحترافية. اكتب إيميل احترافي بناءً على الطلب التالي:

"{user_input}"

اكتب:
1. **Subject (الموضوع):** عنوان واضح وجذاب
2. **Body (المحتوى):** الإيميل كامل بتنسيق احترافي
3. **Tone:** رسمي واحترافي

اكتب بالعربية إلا لو المستخدم طلب الإنجليزية."""

        output = await llm_client.generate(prompt, provider="auto")
        return {"status": "success", "output": output, "tokens_deducted": self.cost}


class DocumentWriterTool(BaseTool):
    """Creates structured documents."""

    @property
    def name(self) -> str:
        return "/write_document"

    @property
    def description(self) -> str:
        return "Creates structured documents (reports, proposals, articles) with proper formatting and sections."

    @property
    def cost(self) -> int:
        return 2

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"""أنت كاتب محتوى محترف. اكتب مستند منظم بناءً على الطلب:

"{user_input}"

اكتب مستند احترافي يحتوي على:
1. عنوان رئيسي
2. ملخص تنفيذي
3. أقسام منظمة مع عناوين فرعية
4. نقاط رئيسية في كل قسم
5. خاتمة وتوصيات

استخدم Markdown formatting."""

        output = await llm_client.generate(prompt, provider="auto", max_tokens=6000)
        return {"status": "success", "output": output, "tokens_deducted": self.cost}


class CodeGeneratorTool(BaseTool):
    """Generates code from description."""

    @property
    def name(self) -> str:
        return "/generate_code"

    @property
    def description(self) -> str:
        return "Generates clean, documented code in any programming language from a description. Supports Python, JavaScript, HTML/CSS, SQL, and more."

    @property
    def cost(self) -> int:
        return 2

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"""أنت مبرمج خبير. اكتب كود احترافي بناءً على الطلب:

"{user_input}"

المطلوب:
1. كود نظيف ومنظم مع Comments
2. اتبع Best Practices
3. أضف شرح مختصر للكود
4. اكتب بأفضل ممارسات اللغة المطلوبة
5. إذا لم يحدد المستخدم لغة، استخدم Python"""

        output = await llm_client.generate(prompt, provider="auto", max_tokens=6000)
        return {"status": "success", "output": output, "tokens_deducted": self.cost}


class StudyPlanTool(BaseTool):
    """Creates personalized study plans."""

    @property
    def name(self) -> str:
        return "/study_plan"

    @property
    def description(self) -> str:
        return "Creates a personalized study plan with timeline, resources, and milestones for any topic or skill."

    @property
    def cost(self) -> int:
        return 1

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"""أنت مستشار تعليمي خبير. اصنع خطة دراسة تفصيلية لـ:

"{user_input}"

اكتب:
1. **الهدف:** ملخص واضح
2. **المدة:** الجدول الزمني المقترح
3. **المراحل:** مقسمة لأسابيع
4. **المصادر:** كتب ومواقع وكورسات مجانية
5. **نصائح:** نصائح عملية للنجاح
6. **الأدوات:** أدوات وبرامج مفيدة

استخدم Markdown formatting وEmojis."""

        output = await llm_client.generate(prompt, provider="auto")
        return {"status": "success", "output": output, "tokens_deducted": self.cost}


class CVBuilderTool(BaseTool):
    """Generates professional CVs/resumes."""

    @property
    def name(self) -> str:
        return "/cv_builder"

    @property
    def description(self) -> str:
        return "Creates a professional CV/resume in Markdown format. Provide your info and get a polished resume."

    @property
    def cost(self) -> int:
        return 2

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"""أنت خبير في كتابة السير الذاتية (CV). بناءً على المعلومات التالية، اكتب CV احترافي:

"{user_input}"

اكتب CV يحتوي على:
1. **الاسم والمعلومات الشخصية**
2. **الملخص المهني** (Professional Summary)
3. **الخبرات العملية** (مرتبة من الأحدث)
4. **التعليم**
5. **المهارات** (Technical & Soft Skills)
6. **الشهادات** (إن وجدت)
7. **اللغات**

استخدم Markdown formatting احترافي. اكتب بالعربية والإنجليزية."""

        output = await llm_client.generate(prompt, provider="auto", max_tokens=4000)
        return {"status": "success", "output": output, "tokens_deducted": self.cost}
