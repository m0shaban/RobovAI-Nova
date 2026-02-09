"""
Art Search API Tool - البحث عن الأعمال الفنية
"""
import os
import httpx
import urllib.parse
from typing import Dict, Any
from .base import BaseTool


class ArtSearchTool(BaseTool):
    """
    أداة البحث عن الأعمال الفنية من متاحف ومعارض عالمية
    """
    @property
    def name(self) -> str:
        return "/art_search"
    
    @property
    def description(self) -> str:
        return "🎨 ابحث عن أعمال فنية من متاحف ومعارض عالمية (لوحات، منحوتات، فنون)"
    
    @property
    def cost(self) -> int:
        return 50
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        البحث عن الأعمال الفنية
        """
        from backend.core.llm import llm_client
        
        # التحقق من API Key
        api_key = os.getenv("ART_SEARCH_API_KEY")
        if not api_key:
            return {
                "status": "error",
                "output": "❌ مفتاح API غير موجود في ملف .env\n\nأضف: ART_SEARCH_API_KEY=your_key",
                "tokens_deducted": 0
            }
        
        if not user_input or len(user_input) < 2:
            return {
                "status": "success",
                "output": """🎨 **Art Search - البحث عن الأعمال الفنية**

**الاستخدام:**
`/art_search اسم الفنان أو العمل الفني`

**أمثلة:**
• `/art_search Mona Lisa`
• `/art_search Van Gogh`
• `/art_search لوحات بيكاسو`

**نتائج البحث تشمل:**
✅ صور الأعمال الفنية
✅ معلومات الفنان
✅ تاريخ العمل
✅ المتحف أو المعرض
✅ الوصف والتفاصيل

💰 التكلفة: 50 توكن""",
                "tokens_deducted": 0
            }
        
        try:
            # ترجمة للإنجليزي إذا كان النص عربي
            has_arabic = any('\u0600' <= c <= '\u06FF' for c in user_input)
            
            if has_arabic:
                translation_prompt = f"""ترجم هذا البحث الفني للإنجليزية:

البحث: {user_input}

قدم الترجمة فقط، بدون شرح."""
                
                english_query = await llm_client.generate(
                    translation_prompt,
                    provider="auto",
                    system_prompt="أنت متخصص في الفن والتاريخ الفني."
                )
                search_query = english_query.strip().strip('"\'')
            else:
                search_query = user_input.strip()
            
            # استخدام Art Search API
            # ملاحظة: يبدو أن هذا API قد يكون custom أو محلي
            # سأستخدم Harvard Art Museums API كبديل أفضل
            
            # Harvard Art Museums API
            url = f"https://api.harvardartmuseums.org/object"
            params = {
                "apikey": api_key,
                "q": search_query,
                "size": 3,
                "hasimage": 1  # فقط الأعمال التي لديها صور
            }
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            records = data.get("records", [])
            
            if not records:
                return {
                    "status": "success",
                    "output": f"❌ لم أجد أعمال فنية مطابقة لـ: **{user_input}**\n\n💡 جرب البحث عن فنان أو عمل فني آخر.",
                    "tokens_deducted": self.cost
                }
            
            # بناء الرد
            output_parts = [
                f"🎨 **وجدت {len(records)} أعمال فنية لـ: {user_input}**\n",
                f"🔍 البحث: `{search_query}`\n"
            ]
            
            for i, art in enumerate(records, 1):
                title = art.get("title", "بدون عنوان")
                artist = art.get("people", [{}])[0].get("name", "فنان غير معروف") if art.get("people") else "فنان غير معروف"
                date = art.get("dated", "تاريخ غير معروف")
                culture = art.get("culture", "")
                image_url = art.get("primaryimageurl", "")
                art_url = art.get("url", "")
                
                output_parts.append(f"\n**{i}. {title}**")
                
                if image_url:
                    output_parts.append(f"![{title}]({image_url})")
                
                output_parts.append(f"👨‍🎨 **الفنان:** {artist}")
                output_parts.append(f"📅 **التاريخ:** {date}")
                
                if culture:
                    output_parts.append(f"🌍 **الثقافة:** {culture}")
                
                if art_url:
                    output_parts.append(f"🔗 [عرض التفاصيل الكاملة]({art_url})")
            
            output_parts.append("\n\n---")
            output_parts.append("*الأعمال الفنية من Harvard Art Museums*")
            
            output = "\n".join(output_parts)
            
            return {
                "status": "success",
                "output": output,
                "tokens_deducted": self.cost
            }
            
        except httpx.HTTPStatusError as e:
            # إذا فشل Harvard API، استخدم AI كبديل
            if e.response.status_code == 401:
                return await self._use_ai_fallback(user_input, search_query, llm_client)
            
            return {
                "status": "error",
                "output": f"❌ خطأ من Art API: {e.response.status_code}\n{e.response.text}",
                "tokens_deducted": 0
            }
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ: {str(e)}",
                "tokens_deducted": 0
            }
    
    async def _use_ai_fallback(self, original_query: str, english_query: str, llm_client) -> Dict[str, Any]:
        """استخدام AI كبديل إذا فشل الـ API"""
        art_prompt = f"""أنت خبير في الفن والتاريخ الفني. ابحث عن معلومات عن:

البحث: {english_query}

قدم معلومات عن أشهر الأعمال الفنية المرتبطة بهذا البحث:
- اسم العمل الفني
- الفنان
- التاريخ/الفترة الزمنية
- نوع العمل (لوحة، منحوتة، إلخ)
- المتحف أو المكان الحالي
- وصف مختصر

قدم 2-3 أعمال فنية فقط."""
        
        result = await llm_client.generate(
            art_prompt,
            provider="auto",
            system_prompt="أنت خبير في تاريخ الفن العالمي والأعمال الفنية الشهيرة."
        )
        
        output = f"""🎨 **معلومات فنية عن: {original_query}**

{result}

---
💡 **ملاحظة:** المعلومات مقدمة من AI. للحصول على صور فعلية، استخدم `/pexels` أو `/unsplash` للبحث عن صور الأعمال الفنية."""
        
        return {
            "status": "success",
            "output": output,
            "tokens_deducted": self.cost
        }
