"""
Unsplash Image Search Tool - يبحث عن صور فوتوغرافية حقيقية من Unsplash
"""
import os
import httpx
import urllib.parse
from typing import Dict, Any
from .base import BaseTool


class UnsplashSearchTool(BaseTool):
    """
    أداة البحث عن صور حقيقية من Unsplash
    """
    @property
    def name(self) -> str:
        return "/unsplash"
    
    @property
    def description(self) -> str:
        return "🔍 ابحث عن صور فوتوغرافية حقيقية واحترافية من Unsplash (مناسب للمناظر الطبيعية، الأشخاص، المدن، الحيوانات، إلخ)"
    
    @property
    def cost(self) -> int:
        return 50
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        البحث في Unsplash عن صور حقيقية
        
        الخطوات:
        1. التحقق من وجود API key
        2. ترجمة النص العربي للإنجليزية (إذا لزم)
        3. البحث في Unsplash
        4. إرجاع أفضل 3 صور
        """
        from backend.core.llm import llm_client
        
        # التحقق من API Key
        api_key = os.getenv("UNSPLASH_ACCESS_KEY")
        if not api_key:
            return {
                "status": "error",
                "output": "❌ مفتاح API غير موجود في ملف .env\n\nأضف: UNSPLASH_ACCESS_KEY=your_key",
                "tokens_deducted": 0
            }
        
        try:
            # ترجمة للإنجليزي إذا كان النص عربي
            has_arabic = any('\u0600' <= c <= '\u06FF' for c in user_input)
            
            if has_arabic:
                translation_prompt = f"""ترجم هذا الوصف للإنجليزية للبحث عن صور:

الوصف: {user_input}

قدم كلمات البحث فقط بالإنجليزية، بدون شرح. استخدم كلمات بسيطة ومباشرة."""
                
                english_query = await llm_client.generate(
                    translation_prompt,
                    provider="groq",
                    system_prompt="أنت مترجم محترف."
                )
                search_query = english_query.strip().strip('"\'')
            else:
                search_query = user_input.strip()
            
            # البحث في Unsplash API
            encoded_query = urllib.parse.quote(search_query)
            url = f"https://api.unsplash.com/search/photos?query={encoded_query}&per_page=3&orientation=landscape"
            
            headers = {
                "Authorization": f"Client-ID {api_key}"
            }
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
            
            # معالجة النتائج
            results = data.get("results", [])
            
            if not results:
                return {
                    "status": "success",
                    "output": f"❌ لم أجد صور مطابقة لـ: **{user_input}**\n\n💡 جرب وصفاً آخر أو استخدم `/generate_image` لتوليد صورة بالذكاء الاصطناعي.",
                    "tokens_deducted": self.cost
                }
            
            # بناء الرد
            output_parts = [
                f"📸 **وجدت {len(results)} صور احترافية لـ: {user_input}**\n",
                f"🔍 كلمات البحث: `{search_query}`\n"
            ]
            
            for i, photo in enumerate(results, 1):
                image_url = photo["urls"]["regular"]
                photographer = photo["user"]["name"]
                photographer_url = photo["user"]["links"]["html"]
                photo_link = photo["links"]["html"]
                
                output_parts.append(f"\n**الصورة {i}:**")
                output_parts.append(f"![Photo by {photographer}]({image_url})")
                output_parts.append(f"📷 بواسطة: [{photographer}]({photographer_url})")
                output_parts.append(f"🔗 [عرض على Unsplash]({photo_link})")
            
            output_parts.append("\n\n---")
            output_parts.append("*جميع الصور من Unsplash - مجانية للاستخدام التجاري والشخصي*")
            
            output = "\n".join(output_parts)
            
            return {
                "status": "success",
                "output": output,
                "tokens_deducted": self.cost
            }
            
        except httpx.HTTPStatusError as e:
            return {
                "status": "error",
                "output": f"❌ خطأ من Unsplash API: {e.response.status_code}\n{e.response.text}",
                "tokens_deducted": 0
            }
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ: {str(e)}",
                "tokens_deducted": 0
            }
