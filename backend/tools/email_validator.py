"""
Email Validator Tool - التحقق من صحة البريد الإلكتروني
"""
import os
import httpx
from typing import Dict, Any
from .base import BaseTool


class EmailValidatorTool(BaseTool):
    """
    أداة التحقق من صحة البريد الإلكتروني
    """
    @property
    def name(self) -> str:
        return "/email_check"
    
    @property
    def description(self) -> str:
        return "📧 التحقق من البريد الإلكتروني - فحص صحة وجودة الإيميل"
    
    @property
    def cost(self) -> int:
        return 20
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        التحقق من صحة البريد الإلكتروني
        """
        
        if not user_input or "@" not in user_input:
            return {
                "status": "success",
                "output": """📧 **التحقق من البريد الإلكتروني**

**الاستخدام:**
`/email_check [email]`

**أمثلة:**
• `/email_check user@example.com`
• `/email_check test@gmail.com`

**الفحوصات:**
✅ صحة التنسيق
✅ وجود النطاق (Domain)
✅ صحة MX Records
✅ اكتشاف الإيميلات المؤقتة

💰 التكلفة: 20 توكن""",
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
            email = user_input.strip()
            
            # استخدام Amdoren Email Validation API
            url = f"https://www.amdoren.com/api/email-validator.php"
            params = {
                "api_key": api_key,
                "email": email
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
            
            if data.get("error"):
                return {
                    "status": "error",
                    "output": f"❌ خطأ: {data.get('error_message', 'Unknown error')}",
                    "tokens_deducted": 0
                }
            
            is_valid = data.get("valid", False)
            
            output = f"""📧 **نتيجة فحص البريد الإلكتروني**

**الإيميل:** `{email}`

**الحالة:** {"✅ صالح" if is_valid else "❌ غير صالح"}

**التفاصيل:**
• التنسيق: {"✅ صحيح" if data.get("format_valid") else "❌ خاطئ"}
• النطاق: {"✅ موجود" if data.get("domain_valid") else "❌ غير موجود"}
• MX Records: {"✅ صحيح" if data.get("mx_found") else "❌ غير موجود"}

{"⚠️ **تحذير:** هذا إيميل مؤقت" if data.get("disposable") else ""}

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
