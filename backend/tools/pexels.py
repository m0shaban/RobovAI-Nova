"""
Pexels Image Search Tool - يبحث عن صور فوتوغرافية حقيقية من Pexels
"""
import os
import httpx
import urllib.parse
from typing import Dict, Any
from .base import BaseTool


class PexelsSearchTool(BaseTool):
    """
    أداة البحث عن صور حقيقية من Pexels
    """
    @property
    def name(self) -> str:
        return "/pexels"
    
    @property
    def description(self) -> str:
        return "📸 ابحث عن صور فوتوغرافية مجانية من Pexels (مكتبة ضخمة + فيديوهات)"
    
    @property
    def cost(self) -> int:
        return 40  # أرخص من Unsplash
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        البحث في Pexels عن صور حقيقية
        """
        from backend.core.llm import llm_client
        
        # التحقق من API Key
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            return {
                "status": "error",
                "output": "❌ مفتاح API غير موجود في ملف .env\n\nأضف: PEXELS_API_KEY=your_key",
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
            
            # البحث في Pexels API
            encoded_query = urllib.parse.quote(search_query)
            url = f"https://api.pexels.com/v1/search?query={encoded_query}&per_page=3&orientation=landscape"
            
            headers = {
                "Authorization": api_key
            }
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
            
            # معالجة النتائج
            photos = data.get("photos", [])
            
            if not photos:
                return {
                    "status": "success",
                    "output": f"❌ لم أجد صور مطابقة لـ: **{user_input}**\n\n💡 جرب وصفاً آخر أو استخدم `/unsplash` أو `/generate_image`.",
                    "tokens_deducted": self.cost
                }
            
            # بناء الرد
            output_parts = [
                f"📸 **وجدت {len(photos)} صور من Pexels لـ: {user_input}**\n",
                f"🔍 كلمات البحث: `{search_query}`\n"
            ]
            
            for i, photo in enumerate(photos, 1):
                image_url = photo["src"]["large"]  # Large size
                photographer = photo["photographer"]
                photographer_url = photo["photographer_url"]
                photo_link = photo["url"]
                
                output_parts.append(f"\n**الصورة {i}:**")
                output_parts.append(f"![Photo by {photographer}]({image_url})")
                output_parts.append(f"📷 بواسطة: [{photographer}]({photographer_url})")
                output_parts.append(f"🔗 [عرض على Pexels]({photo_link})")
            
            output_parts.append("\n\n---")
            output_parts.append("*جميع الصور من Pexels - مجانية بالكامل للاستخدام التجاري*")
            
            output = "\n".join(output_parts)
            
            return {
                "status": "success",
                "output": output,
                "tokens_deducted": self.cost
            }
            
        except httpx.HTTPStatusError as e:
            return {
                "status": "error",
                "output": f"❌ خطأ من Pexels API: {e.response.status_code}\n{e.response.text}",
                "tokens_deducted": 0
            }
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ: {str(e)}",
                "tokens_deducted": 0
            }
