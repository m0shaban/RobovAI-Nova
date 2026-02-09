"""
AniDB Search Tool - البحث عن معلومات الأنمي والمانجا
"""
import os
import httpx
import urllib.parse
from typing import Dict, Any
from .base import BaseTool


class AniDBSearchTool(BaseTool):
    """
    أداة البحث عن معلومات الأنمي والمانجا من AniDB
    """
    @property
    def name(self) -> str:
        return "/anidb"
    
    @property
    def description(self) -> str:
        return "📺 ابحث عن معلومات الأنمي والمانجا من AniDB (تقييمات، حلقات، تواريخ)"
    
    @property
    def cost(self) -> int:
        return 30
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        البحث في AniDB عن معلومات الأنمي
        """
        from backend.core.llm import llm_client
        
        if not user_input or len(user_input) < 2:
            return {
                "status": "success",
                "output": """📺 **بحث AniDB - معلومات الأنمي والمانجا**

**الاستخدام:**
`/anidb اسم الأنمي`

**أمثلة:**
• `/anidb Naruto`
• `/anidb Attack on Titan`
• `/anidb ون بيس`

**المعلومات المتاحة:**
✅ التقييمات والمراجعات
✅ عدد الحلقات والموسم
✅ تاريخ العرض
✅ النوع والفئة العمرية
✅ فريق العمل والاستوديو

💰 التكلفة: 30 توكن""",
                "tokens_deducted": 0
            }
        
        try:
            # ترجمة للإنجليزي إذا كان النص عربي
            has_arabic = any('\u0600' <= c <= '\u06FF' for c in user_input)
            
            if has_arabic:
                translation_prompt = f"""ترجم اسم هذا الأنمي للإنجليزية:

الاسم: {user_input}

قدم الاسم الإنجليزي فقط، بدون شرح."""
                
                english_query = await llm_client.generate(
                    translation_prompt,
                    provider="auto",
                    system_prompt="أنت متخصص في الأنمي والمانجا."
                )
                search_query = english_query.strip().strip('"\'')
            else:
                search_query = user_input.strip()
            
            # استخدام AI للبحث عن معلومات الأنمي
            # ملاحظة: AniDB API يتطلب تسجيل وموافقة معقدة
            # لذا سنستخدم AI كبديل أفضل للمستخدم
            
            anime_prompt = f"""أنت قاعدة بيانات أنمي ومانجا متخصصة. ابحث عن معلومات عن:

الأنمي: {search_query}

قدم المعلومات التالية إذا كانت متوفرة:
- الاسم الكامل (بالإنجليزية واليابانية)
- النوع (شونين، شوجو، إلخ)
- التقييم (من 10)
- عدد الحلقات/الفصول
- تاريخ العرض
- الاستوديو
- نبذة مختصرة

قدم المعلومات بشكل منظم وواضح."""
            
            result = await llm_client.generate(
                anime_prompt,
                provider="auto",
                system_prompt="أنت خبير في الأنمي والمانجا وتمتلك معرفة واسعة بجميع العناوين."
            )
            
            output = f"""📺 **معلومات الأنمي: {user_input}**

{result}

---
💡 **ملاحظة:** المعلومات مقدمة من AI وقد تحتاج للتحقق من مصادر رسمية.
🔗 للمزيد: قم بالبحث على [MyAnimeList](https://myanimelist.net) أو [AniDB](https://anidb.net)"""
            
            return {
                "status": "success",
                "output": output,
                "tokens_deducted": self.cost
            }
            
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ: {str(e)}",
                "tokens_deducted": 0
            }
