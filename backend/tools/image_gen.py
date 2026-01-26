from typing import Dict, Any
from .base import BaseTool
from backend.core.llm import llm_client
import urllib.parse
import httpx
import os
import base64

class ImageGenTool(BaseTool):
    """
    توليد صور باستخدام Pollinations.ai - جودة احترافية
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

🎁 **مجاني تماماً!** Powered by Pollinations.ai - FLUX Model""",
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
            
            # Get API key
            api_key = os.getenv("POLLINATIONS_API_KEY")
            if not api_key:
                return {
                    "status": "error",
                    "output": "❌ POLLINATIONS_API_KEY not set in .env file",
                    "tokens_deducted": 0
                }
            
            # إنشاء seed للتفرد
            import random
            import time
            seed = int(time.time() * 1000) % 1000000
            
            # New Pollinations.ai API with authentication
            encoded_prompt = urllib.parse.quote(english_prompt)
            url = f"https://gen.pollinations.ai/image/{encoded_prompt}"
            
            params = {
                "model": "flux",        # High quality model
                "width": 1024,
                "height": 1024,
                "seed": seed,
                "enhance": "true",      # AI prompt enhancement
                "safe": "false"         # Allow creative content
            }
            
            headers = {
                "Authorization": f"Bearer {api_key}"
            }
            
            # Download image from Pollinations.ai
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                image_bytes = response.content
            
            # Upload to ImgBB for permanent storage
            imgbb_key = os.getenv("IMGBB_API_KEY")
            if not imgbb_key:
                return {
                    "status": "error",
                    "output": "❌ IMGBB_API_KEY not set in .env file",
                    "tokens_deducted": 0
                }
            
            # Encode image to base64
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Upload to ImgBB
            upload_url = "https://api.imgbb.com/1/upload"
            upload_data = {
                "key": imgbb_key,
                "image": image_b64,
                "name": f"robovai_{seed}"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                upload_response = await client.post(upload_url, data=upload_data)
                upload_response.raise_for_status()
                upload_result = upload_response.json()
            
            if upload_result.get("success"):
                image_url = upload_result["data"]["url"]
                display_url = upload_result["data"]["display_url"]
                
                # إرجاع الصورة بصيغة Markdown
                output = f"""🎨 **تم توليد الصورة بنجاح!**

📝 **الوصف الأصلي:** {user_input}
🌐 **Prompt:** {english_prompt}
🤖 **Model:** FLUX (High Quality)

![Generated Image]({display_url})

---
✨ **Powered by Pollinations.ai** | 📦 **Hosted by ImgBB**
🔗 Direct Link: {image_url}"""
                
                return {
                    "status": "success",
                    "output": output,
                    "image_url": image_url,
                    "display_url": display_url,
                    "tokens_deducted": self.cost
                }
            else:
                return {
                    "status": "error",
                    "output": f"❌ فشل رفع الصورة لـ ImgBB: {upload_result}",
                    "tokens_deducted": 0
                }
            
        except httpx.HTTPStatusError as e:
            return {
                "status": "error",
                "output": f"❌ خطأ من API: {e.response.status_code}\n{e.response.text[:200]}",
                "tokens_deducted": 0
            }
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ في توليد الصورة: {str(e)}",
                "tokens_deducted": 0
            }
