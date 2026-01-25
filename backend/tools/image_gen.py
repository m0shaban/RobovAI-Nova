from typing import Dict, Any
from .base import BaseTool
from backend.core.llm import llm_client
import urllib.parse

class ImageGenTool(BaseTool):
    """
    توليد صور باستخدام AI - Pollinations.ai مجاني تماماً
    """
    @property
    def name(self): return "/generate_image"
    @property
    def description(self): return "توليد صورة بالذكاء الاصطناعي من وصف نصي"
    @property
    def cost(self): return 0  # مجاني!
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        user_input: وصف الصورة بالعربي أو الإنجليزي
        """
        if not user_input or len(user_input) < 3:
            return {
                "status": "success",
                "output": """🎨 **مولد الصور بالذكاء الاصطناعي**

**الاستخدام:**
`/generate_image وصف الصورة`

**أمثلة:**
• `/generate_image أسد مخطط في الغابة`
• `/generate_image sunset over ocean, 4k realistic`
• `/generate_image cute cat wearing sunglasses`

**نصائح:**
✅ استخدم تفاصيل دقيقة للنتائج الأفضل
✅ الإنجليزي يعطي نتائج أفضل عادة
✅ أضف كلمات مثل "realistic", "4k", "detailed"

🎁 **مجاني تماماً!** Powered by Pollinations.ai""",
                "tokens_deducted": 0
            }
        
        try:
            # ترجمة للإنجليزي إذا كان النص عربي
            has_arabic = any('\u0600' <= c <= '\u06FF' for c in user_input)
            
            if has_arabic:
                # ترجمة AI للإنجليزي لأفضل نتائج
                translation_prompt = f"""ترجم هذا الوصف للإنجليزي بطريقة احترافية لتوليد صور AI:

الوصف: {user_input}

قدم الترجمة فقط، بدون شرح. أضف كلمات مثل realistic, detailed, high quality إذا كانت مناسبة."""
                
                english_prompt = await llm_client.generate(
                    translation_prompt,
                    provider="groq",
                    system_prompt="أنت مترجم محترف لأوصاف توليد الصور بالذكاء الاصطناعي."
                )
                english_prompt = english_prompt.strip().strip('"\'')
            else:
                english_prompt = user_input.strip()
            
            # إنشاء URL للصورة من Pollinations (v2 API)
            # الـ API الجديد بيستخدم pollinations.ai مش image.pollinations.ai
            encoded_prompt = urllib.parse.quote(english_prompt)
            
            # إضافة seed عشوائي لتجنب الصورة الأولية
            import random
            import time
            seed = int(time.time() * 1000) % 1000000  # استخدام timestamp للتفرد
            
            # New API format
            image_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&seed={seed}&nologo=true"
            
            # إرجاع الصورة بصيغة Markdown
            output = f"""🎨 **تم توليد الصورة!**

📝 **الوصف الأصلي:** {user_input}
🌐 **Prompt:** {english_prompt}

![Generated Image]({image_url})

---
💡 **تلميح:** الصورة قد تستغرق ثوانٍ قليلة للتحميل في المرة الأولى

✨ Powered by Pollinations.ai (Free & Unlimited)"""
            
            return {
                "status": "success",
                "output": output,
                "tokens_deducted": self.cost
            }
            
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ في توليد الصورة: {str(e)}",
                "tokens_deducted": 0
            }
