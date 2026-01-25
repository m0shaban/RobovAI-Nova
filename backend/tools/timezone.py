"""
Timezone Converter Tool - تحويل المناطق الزمنية
"""
import os
import httpx
from typing import Dict, Any
from datetime import datetime
from .base import BaseTool


class TimezoneTool(BaseTool):
    """
    أداة تحويل المناطق الزمنية
    """
    @property
    def name(self) -> str:
        return "/timezone"
    
    @property
    def description(self) -> str:
        return "🌍 تحويل المناطق الزمنية - معرفة الوقت في أي مدينة"
    
    @property
    def cost(self) -> int:
        return 15
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        تحويل المناطق الزمنية
        """
        
        if not user_input or len(user_input) < 2:
            return {
                "status": "success",
                "output": """🌍 **تحويل المناطق الزمنية**

**الاستخدام:**
`/timezone [city]`

**أمثلة:**
• `/timezone Cairo`
• `/timezone New York`
• `/timezone Tokyo`
• `/timezone London`

**المعلومات المتاحة:**
✅ الوقت الحالي
✅ المنطقة الزمنية
✅ فرق التوقيت عن UTC
✅ التوقيت الصيفي

💰 التكلفة: 15 توكن""",
                "tokens_deducted": 0
            }
        
        # التحقق من API Key
        api_key = os.getenv("AMDOREN_API_KEY")
        if not api_key:
            return {
                "status": "error",
                "output": "❌ مفتاح API غير موجود في ملف .env\n\nأضف: AMDOREN_API_KEY=your_key",
                "tokens_deducted": 0
            }
        
        try:
            city = user_input.strip()
            
            # استخدام Amdoren Timezone API
            url = f"https://www.amdoren.com/api/timezone.php"
            params = {
                "api_key": api_key,
                "loc": city
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            if data.get("error"):
                return {
                    "status": "error",
                    "output": f"❌ خطأ: {data.get('error_message', 'City not found')}",
                    "tokens_deducted": 0
                }
            
            timezone = data.get("timezone", "N/A")
            current_time = data.get("time", "N/A")
            utc_offset = data.get("utc_offset", "N/A")
            
            output = f"""🌍 **معلومات المنطقة الزمنية**

**المدينة:** {city}
**المنطقة الزمنية:** {timezone}

⏰ **الوقت الحالي:** {current_time}
🌐 **فرق التوقيت:** UTC{utc_offset}

---
💡 Powered by Amdoren"""
            
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
