"""
DDownload Tool - رفع وإدارة الملفات على DDownload.com
"""
import os
import httpx
from typing import Dict, Any
from .base import BaseTool


class DDownloadTool(BaseTool):
    """
    أداة DDownload - رفع وإدارة الملفات
    """
    @property
    def name(self) -> str:
        return "/ddownload"
    
    @property
    def description(self) -> str:
        return "📦 DDownload - رفع وإدارة الملفات على DDownload.com (تخزين سحابي)"
    
    @property
    def cost(self) -> int:
        return 30
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        إدارة الملفات على DDownload
        """
        
        if not user_input or len(user_input) < 2:
            return {
                "status": "success",
                "output": """📦 **DDownload - التخزين السحابي**

**الاستخدام:**
`/ddownload info` - معلومات الحساب
`/ddownload stats` - إحصائيات الحساب
`/ddownload list` - قائمة الملفات

**المميزات:**
✅ تخزين سحابي مع إحصائيات
✅ إدارة المجلدات
✅ تتبع التحميلات والمشاهدات
✅ دعم Premium

⚠️ **ملاحظة:** يتطلب API key من حسابك على DDownload

💰 التكلفة: 30 توكن""",
                "tokens_deducted": 0
            }
        
        # التحقق من API Key
        api_key = os.getenv("DDOWNLOAD_API_KEY")
        if not api_key:
            return {
                "status": "error",
                "output": "❌ مفتاح API غير موجود في ملف .env\n\nأضف: DDOWNLOAD_API_KEY=your_key",
                "tokens_deducted": 0
            }
        
        try:
            command = user_input.lower().strip()
            
            if command == "info":
                return await self._get_account_info(api_key)
            elif command == "stats":
                return await self._get_account_stats(api_key)
            elif command == "list":
                return await self._list_files(api_key)
            else:
                return {
                    "status": "success",
                    "output": """💡 **الأوامر المتاحة:**

• `/ddownload info` - معلومات الحساب
• `/ddownload stats` - إحصائيات آخر 7 أيام
• `/ddownload list` - قائمة الملفات

🔜 **قريباً:** رفع الملفات مباشرة""",
                    "tokens_deducted": self.cost
                }
            
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ: {str(e)}",
                "tokens_deducted": 0
            }
    
    async def _get_account_info(self, api_key: str) -> Dict[str, Any]:
        """الحصول على معلومات الحساب"""
        try:
            url = f"https://api-v2.ddownload.com/api/account/info?key={api_key}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            if data.get("status") != 200:
                return {
                    "status": "error",
                    "output": f"❌ خطأ: {data.get('msg', 'Unknown error')}",
                    "tokens_deducted": 0
                }
            
            result = data.get("result", {})
            
            # تحويل البيانات لصيغة قابلة للقراءة
            storage_used = int(result.get("storage_used", 0)) / (1024**3)  # GB
            traffic_used = int(result.get("traffic_used", 0)) / (1024**3)  # GB
            
            output = f"""📦 **معلومات حساب DDownload**

**البريد الإلكتروني:** {result.get('email', 'غير متاح')}
**نوع الحساب:** {'Premium' if result.get('premium_expire') else 'Free'}
**المساحة المستخدمة:** {storage_used:.2f} GB
**الترافيك المستخدم:** {traffic_used:.2f} GB
**الرصيد:** ${result.get('balance', '0')}

{f"**انتهاء Premium:** {result.get('premium_expire')}" if result.get('premium_expire') else ""}

🔗 **الرابط:** https://ddownload.com/dashboard"""
            
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
    
    async def _get_account_stats(self, api_key: str) -> Dict[str, Any]:
        """الحصول على إحصائيات الحساب"""
        try:
            url = f"https://api-v2.ddownload.com/api/account/stats?key={api_key}&last=7"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            if data.get("status") != 200:
                return {
                    "status": "error",
                    "output": f"❌ خطأ: {data.get('msg', 'Unknown error')}",
                    "tokens_deducted": 0
                }
            
            stats = data.get("result", [])
            
            if not stats:
                return {
                    "status": "success",
                    "output": "📊 لا توجد إحصائيات متاحة حالياً.",
                    "tokens_deducted": self.cost
                }
            
            # حساب الإجماليات
            total_downloads = sum(int(day.get("downloads", 0)) for day in stats)
            total_views = sum(int(day.get("views", 0)) for day in stats)
            
            output = f"""📊 **إحصائيات آخر 7 أيام**

**إجمالي التحميلات:** {total_downloads}
**إجمالي المشاهدات:** {total_views}

**آخر يوم ({stats[0].get('day')}):**
• التحميلات: {stats[0].get('downloads', 0)}
• المشاهدات: {stats[0].get('views', 0)}

🔗 **المزيد:** https://ddownload.com/dashboard"""
            
            return {
                "status": "success",
                "output": output,
                "tokens_deducted": self.cost
            }
            
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ في جلب الإحصائيات: {str(e)}",
                "tokens_deducted": 0
            }
    
    async def _list_files(self, api_key: str) -> Dict[str, Any]:
        """عرض قائمة الملفات"""
        try:
            url = f"https://api-v2.ddownload.com/api/file/list?key={api_key}&page=1&per_page=10"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            if data.get("status") != 200:
                return {
                    "status": "error",
                    "output": f"❌ خطأ: {data.get('msg', 'Unknown error')}",
                    "tokens_deducted": 0
                }
            
            files = data.get("result", [])
            
            if not files:
                return {
                    "status": "success",
                    "output": "📁 لا توجد ملفات في حسابك حالياً.",
                    "tokens_deducted": self.cost
                }
            
            files_list = []
            for file in files[:5]:  # أول 5 ملفات
                size_mb = int(file.get("size", 0)) / (1024**2)
                files_list.append(f"""**{file.get('name')}**
• الحجم: {size_mb:.2f} MB
• التحميلات: {file.get('downloads', 0)}
• الرابط: https://ddownload.com/{file.get('filecode')}
""")
            
            output = f"""📁 **قائمة الملفات (أول 5)**

{chr(10).join(files_list)}

💡 **المزيد:** https://ddownload.com/dashboard"""
            
            return {
                "status": "success",
                "output": output,
                "tokens_deducted": self.cost
            }
            
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ في جلب قائمة الملفات: {str(e)}",
                "tokens_deducted": 0
            }
