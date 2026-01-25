"""
OpenRouter Image Generation Tool - توليد صور باستخدام نماذج AI متقدمة
"""
import os
import httpx
import base64
from typing import Dict, Any
from .base import BaseTool


class OpenRouterImageTool(BaseTool):
    """
    أداة توليد صور باستخدام OpenRouter (نماذج متعددة)
    """
    @property
    def name(self) -> str:
        return "/openrouter_image"
    
    @property
    def description(self) -> str:
        return "🎨 توليد صور احترافية بالذكاء الاصطناعي عبر OpenRouter (Gemini, FLUX, وأكثر)"
    
    @property
    def cost(self) -> int:
        return 100  # أغلى لأنه يستخدم نماذج متقدمة
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        توليد صورة باستخدام OpenRouter API
        """
        from backend.core.llm import llm_client
        
        # التحقق من API Key
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return {
                "status": "error",
                "output": "❌ مفتاح API غير موجود في ملف .env\n\nأضف: OPENROUTER_API_KEY=your_key",
                "tokens_deducted": 0
            }
        
        if not user_input or len(user_input) < 3:
            return {
                "status": "success",
                "output": """🎨 **مولد الصور المتقدم - OpenRouter**

**الاستخدام:**
`/openrouter_image وصف الصورة`

**النماذج المدعومة:**
• Google Gemini 2.5 Flash (سريع)
• FLUX.2 Pro (احترافي)
• Sourceful Riverflow (إبداعي)

**أمثلة:**
• `/openrouter_image قطة لطيفة في الفضاء`
• `/openrouter_image beautiful landscape 4K`

**المميزات:**
✅ جودة عالية جداً
✅ نماذج متعددة
✅ دعم aspect ratios مختلفة (16:9, 4:3, وأكثر)

💰 التكلفة: 100 توكن""",
                "tokens_deducted": 0
            }
        
        try:
            # ترجمة للإنجليزي إذا كان النص عربي
            has_arabic = any('\u0600' <= c <= '\u06FF' for c in user_input)
            
            if has_arabic:
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
            
            # استدعاء OpenRouter API
            url = "https://openrouter.ai/api/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://robovai.tech",  # Optional
                "X-Title": "RobovAI Image Generator"     # Optional
            }
            
            payload = {
                "model": "google/gemini-2.5-flash-image-preview",  # يمكن تغييره
                "messages": [
                    {
                        "role": "user",
                        "content": english_prompt
                    }
                ],
                "modalities": ["image", "text"],
                "image_config": {
                    "aspect_ratio": "1:1",  # يمكن تخصيصه
                    "image_size": "1K"       # 1K, 2K, 4K
                }
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
            
            # استخراج الصورة من الرد
            if data.get("choices"):
                message = data["choices"][0]["message"]
                
                # نص الرد
                text_response = message.get("content", "")
                
                # الصور
                if message.get("images"):
                    images = message["images"]
                    
                    output_parts = [
                        f"🎨 **تم توليد الصورة بنجاح!**\n",
                        f"📝 **الوصف الأصلي:** {user_input}",
                        f"🌐 **Prompt:** {english_prompt}\n"
                    ]
                    
                    for i, image in enumerate(images, 1):
                        image_data_url = image["image_url"]["url"]
                        output_parts.append(f"\n**الصورة {i}:**")
                        output_parts.append(f"![Generated Image {i}]({image_data_url})")
                    
                    if text_response:
                        output_parts.append(f"\n💬 **ملاحظة:** {text_response}")
                    
                    output_parts.append("\n---")
                    output_parts.append("✨ **Powered by OpenRouter** (Gemini 2.5 Flash)")
                    
                    output = "\n".join(output_parts)
                    
                    return {
                        "status": "success",
                        "output": output,
                        "tokens_deducted": self.cost
                    }
                else:
                    return {
                        "status": "error",
                        "output": f"❌ لم يتم توليد صورة. الرد: {text_response}",
                        "tokens_deducted": self.cost // 2
                    }
            else:
                return {
                    "status": "error",
                    "output": "❌ خطأ في الرد من OpenRouter API",
                    "tokens_deducted": 0
                }
            
        except httpx.HTTPStatusError as e:
            return {
                "status": "error",
                "output": f"❌ خطأ من OpenRouter API: {e.response.status_code}\n{e.response.text}",
                "tokens_deducted": 0
            }
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ: {str(e)}",
                "tokens_deducted": 0
            }
