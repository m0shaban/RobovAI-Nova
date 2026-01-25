"""
Wikipedia Tool - البحث في ويكيبيديا
"""
import httpx
from typing import Dict, Any
from .base import BaseTool


class WikipediaTool(BaseTool):
    """
    أداة البحث في ويكيبيديا
    """
    @property
    def name(self) -> str:
        return "/wikipedia"
    
    @property
    def description(self) -> str:
        return "📖 ويكيبيديا - البحث في الموسوعة الحرة (عربي/إنجليزي)"
    
    @property
    def cost(self) -> int:
        return 15
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        البحث في ويكيبيديا
        """
        
        if not user_input or len(user_input) < 2:
            return {
                "status": "success",
                "output": """📖 **ويكيبيديا - الموسوعة الحرة**

**الاستخدام:**
`/wikipedia [search term]`
أو
`/wikipedia ar [search term]` - للبحث بالعربية

**أمثلة:**
• `/wikipedia Python programming`
• `/wikipedia ar مصر`
• `/wikipedia Albert Einstein`

**المميزات:**
✅ ملخص المقالة
✅ رابط المقالة الكاملة
✅ دعم العربية والإنجليزية
✅ معلومات موثوقة

💰 التكلفة: 15 توكن""",
                "tokens_deducted": 0
            }
        
        try:
            # تحديد اللغة
            parts = user_input.split(maxsplit=1)
            if parts[0].lower() == "ar" and len(parts) > 1:
                lang = "ar"
                query = parts[1]
            else:
                lang = "en"
                query = user_input
            
            # البحث في ويكيبيديا
            api_url = f"https://{lang}.wikipedia.org/w/api.php"
            
            # أولاً: البحث عن العنوان
            search_params = {
                "action": "opensearch",
                "search": query,
                "limit": 1,
                "format": "json"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                search_response = await client.get(api_url, params=search_params)
                search_response.raise_for_status()
                search_data = search_response.json()
            
            if not search_data[1]:
                return {
                    "status": "error",
                    "output": f"❌ لم أجد نتائج لـ: **{query}**",
                    "tokens_deducted": 0
                }
            
            title = search_data[1][0]
            page_url = search_data[3][0]
            
            # ثانياً: الحصول على ملخص المقالة
            extract_params = {
                "action": "query",
                "titles": title,
                "prop": "extracts|pageimages",
                "exintro": True,
                "explaintext": True,
                "piprop": "thumbnail",
                "pithumbsize": 300,
                "format": "json"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                extract_response = await client.get(api_url, params=extract_params)
                extract_response.raise_for_status()
                extract_data = extract_response.json()
            
            pages = extract_data.get("query", {}).get("pages", {})
            page = list(pages.values())[0]
            
            extract = page.get("extract", "لا يوجد ملخص متاح")
            thumbnail = page.get("thumbnail", {}).get("source", "")
            
            # تقصير الملخص إذا كان طويلاً
            if len(extract) > 500:
                extract = extract[:500] + "..."
            
            output = f"""📖 **{title}**

**الملخص:**
{extract}

**اللغة:** {"العربية" if lang == "ar" else "English"}

**اقرأ المزيد:**
{page_url}

---
💡 المصدر: ويكيبيديا - الموسوعة الحرة"""
            
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
