"""
ImgBB Tool - رفع الصور على ImgBB (Enhanced)
"""
import os
import httpx
import base64
from typing import Dict, Any
from .base import BaseTool


class ImgBBTool(BaseTool):
    """
    أداة ImgBB - رفع الصور
    """
    @property
    def name(self) -> str:
        return "/imgbb"
    
    @property
    def description(self) -> str:
        return "🖼️ ImgBB - رفع الصور على ImgBB (استضافة صور مجانية)"
    
    @property
    def cost(self) -> int:
        return 20
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        رفع صورة على ImgBB
        """
        
        if not user_input or len(user_input) < 2:
            return {
                "status": "success",
                "output": """🖼️ **ImgBB - استضافة الصور**

**الاستخدام:**
1. ارسل صورة ← سيتم رفعها تلقائياً
2. `/imgbb [رابط صورة]` - رفع من رابط

**المميزات:**
✅ رفع صور مجاني (حتى 32 MB)
✅ روابط مباشرة للصور
✅ صور بأحجام مختلفة
✅ لا يحتاج تسجيل

**كيفية الاستخدام:**
1. ارسل صورة من جهازك
2. أو اكتب: `/imgbb https://example.com/image.jpg`

💰 التكلفة: 20 توكن""",
                "tokens_deducted": 0
            }
        
        # التحقق من API Key
        api_key = os.getenv("IMGBB_API_KEY")
        if not api_key:
            return {
                "status": "error",
                "output": "❌ مفتاح API غير موجود في ملف .env\n\nأضف: IMGBB_API_KEY=your_key",
                "tokens_deducted": 0
            }
        
        try:
            # تحديد نوع المدخل
            if user_input.startswith(('http://', 'https://')):
                # رابط صورة
                return await self._upload_from_url(api_key, user_input)
            elif os.path.exists(user_input):
                # ملف محلي
                return await self._upload_from_file(api_key, user_input)
            elif len(user_input) > 100:
                # قد يكون base64
                return await self._upload_from_base64(api_key, user_input)
            else:
                return {
                    "status": "error",
                    "output": """❌ صيغة غير معروفة

**الصيغ المدعومة:**
• رابط صورة: `https://example.com/image.jpg`
• ملف محلي: `/path/to/image.jpg`
• Base64 data

**الطريقة الأسهل:**
ارسل الصورة مباشرة من جهازك!""",
                    "tokens_deducted": 0
                }
            
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ: {str(e)}",
                "tokens_deducted": 0
            }
    
    async def _upload_from_url(self, api_key: str, image_url: str) -> Dict[str, Any]:
        """رفع صورة من رابط"""
        url = f"https://api.imgbb.com/1/upload"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, data={
                "key": api_key,
                "image": image_url
            })
            
            return await self._process_response(response)
    
    async def _upload_from_file(self, api_key: str, file_path: str) -> Dict[str, Any]:
        """رفع صورة من ملف محلي"""
        url = f"https://api.imgbb.com/1/upload"
        
        # قراءة الملف وتحويله لـ base64
        with open(file_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, data={
                "key": api_key,
                "image": image_data
            })
            
            return await self._process_response(response)
    
    async def _upload_from_base64(self, api_key: str, base64_data: str) -> Dict[str, Any]:
        """رفع صورة من base64"""
        url = f"https://api.imgbb.com/1/upload"
        
        # إزالة البادئة إن وجدت
        if "," in base64_data:
            base64_data = base64_data.split(",")[1]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, data={
                "key": api_key,
                "image": base64_data
            })
            
            return await self._process_response(response)
    
    async def _process_response(self, response) -> Dict[str, Any]:
        """معالجة رد ImgBB"""
        response.raise_for_status()
        result = response.json()
        
        if not result.get("success"):
            return {
                "status": "error",
                "output": f"❌ فشل الرفع: {result.get('error', {}).get('message', 'Unknown error')}",
                "tokens_deducted": 0
            }
        
        data = result.get("data", {})
        
        # حساب الحجم
        size_kb = int(data.get('size', 0)) / 1024
        size_str = f"{size_kb:.2f} KB" if size_kb < 1024 else f"{size_kb/1024:.2f} MB"
        
        output = f"""🖼️ **تم رفع الصورة بنجاح!**

**📷 معلومات الصورة:**
• الاسم: `{data.get('title', 'image')}`
• الحجم: {size_str}
• الأبعاد: {data.get('width')}x{data.get('height')} px

**🔗 الروابط:**

**رابط مباشر (للمشاركة):**
```
{data.get('url')}
```

**رابط العرض:**
{data.get('url_viewer')}

**معاينة:**
![Uploaded]({data.get('display_url')})

---
🗑️ [رابط الحذف]({data.get('delete_url')})
💡 احفظ رابط الحذف إذا كنت تريد حذف الصورة لاحقاً"""
        
        return {
            "status": "success",
            "output": output,
            "direct_url": data.get('url'),
            "display_url": data.get('display_url'),
            "delete_url": data.get('delete_url'),
            "tokens_deducted": self.cost
        }
