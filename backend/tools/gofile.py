"""
Gofile Tool - رفع وإدارة الملفات على Gofile.io
"""
import os
import httpx
from typing import Dict, Any
from .base import BaseTool


class GofileTool(BaseTool):
    """
    أداة Gofile - رفع وإدارة الملفات
    """
    @property
    def name(self) -> str:
        return "/gofile"
    
    @property
    def description(self) -> str:
        return "☁️ Gofile - رفع وإدارة الملفات على Gofile.io (تخزين سحابي مجاني)"
    
    @property
    def cost(self) -> int:
        return 30
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        إدارة الملفات على Gofile
        """
        
        if not user_input or len(user_input) < 2:
            return {
                "status": "success",
                "output": """☁️ **Gofile - التخزين السحابي**

**الاستخدام:**
`/gofile info` - معلومات الحساب
`/gofile upload [file_path]` - رفع ملف
`/gofile list` - عرض الملفات

**المميزات:**
✅ تخزين سحابي مجاني
✅ رفع ملفات بدون حد
✅ إدارة المجلدات
✅ روابط مباشرة

⚠️ **ملاحظة:** يتطلب API token من حسابك على Gofile

💰 التكلفة: 30 توكن""",
                "tokens_deducted": 0
            }
        
        # التحقق من API Token
        api_token = os.getenv("GOFILE_API_TOKEN")
        if not api_token:
            return {
                "status": "error",
                "output": "❌ مفتاح API غير موجود في ملف .env\n\nأضف: GOFILE_API_TOKEN=your_token",
                "tokens_deducted": 0
            }
        
        try:
            command = user_input.lower().strip()
            
            if command == "info":
                return await self._get_account_info(api_token)
            elif command == "list":
                return await self._list_files(api_token)
            else:
                return {
                    "status": "success",
                    "output": """💡 **الأوامر المتاحة:**

• `/gofile info` - معلومات الحساب
• `/gofile list` - قائمة الملفات

🔜 **قريباً:** رفع الملفات مباشرة من الشات""",
                    "tokens_deducted": self.cost
                }
            
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ: {str(e)}",
                "tokens_deducted": 0
            }
    
    async def _get_account_info(self, api_token: str) -> Dict[str, Any]:
        """الحصول على معلومات الحساب"""
        try:
            url = "https://api.gofile.io/accounts/getid"
            headers = {"Authorization": f"Bearer {api_token}"}
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
            
            if data.get("status") != "ok":
                return {
                    "status": "error",
                    "output": f"❌ خطأ: {data.get('message', 'Unknown error')}",
                    "tokens_deducted": 0
                }
            
            account_id = data["data"]
            
            # الحصول على تفاصيل الحساب
            url2 = f"https://api.gofile.io/accounts/{account_id}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response2 = await client.get(url2, headers=headers)
                response2.raise_for_status()
                data2 = response2.json()
            
            account_data = data2.get("data", {})
            
            output = f"""☁️ **معلومات حساب Gofile**

**معرف الحساب:** `{account_id}`
**البريد الإلكتروني:** {account_data.get('email', 'غير متاح')}
**نوع الحساب:** {account_data.get('tier', 'Free')}
**المساحة المستخدمة:** {account_data.get('filesCount', 0)} ملف

🔗 **الرابط:** https://gofile.io/myFiles"""
            
            return {
                "status": "success",
                "output": output,
                "tokens_deducted": self.cost
            }
            
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ في جلب معلومات الحساب: {str(e)}",
                "tokens_deducted": 0
            }
    
    async def _list_files(self, api_token: str) -> Dict[str, Any]:
        """عرض قائمة الملفات"""
        return {
            "status": "success",
            "output": """📁 **قائمة الملفات**

⚠️ هذه الميزة تتطلب معرف المجلد الجذر.

💡 استخدم `/gofile info` لعرض معلومات الحساب أولاً.""",
            "tokens_deducted": self.cost
        }
