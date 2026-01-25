"""
Image-Charts Tool - إنشاء الرسوم البيانية
"""
import urllib.parse
from typing import Dict, Any
from .base import BaseTool


class ImageChartsTool(BaseTool):
    """
    أداة إنشاء الرسوم البيانية باستخدام Image-Charts
    """
    @property
    def name(self) -> str:
        return "/chart"
    
    @property
    def description(self) -> str:
        return "📊 إنشاء رسوم بيانية - pie, bar, line charts وأكثر"
    
    @property
    def cost(self) -> int:
        return 10
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        إنشاء رسم بياني
        """
        
        if not user_input or len(user_input) < 3:
            return {
                "status": "success",
                "output": """📊 **إنشاء الرسوم البيانية**

**الاستخدام:**
`/chart [type] [data] [labels]`

**أنواع الرسوم:**
• `pie` - دائري
• `bar` - أعمدة
• `line` - خطي
• `radar` - راداري

**أمثلة:**
• `/chart pie 60,40 Hello|World`
• `/chart bar 30,60,90 Jan|Feb|Mar`
• `/chart line 10,20,30,25 Q1|Q2|Q3|Q4`

**المميزات:**
✅ رسوم بيانية احترافية
✅ ألوان تلقائية جميلة
✅ مجاني بالكامل
✅ روابط مباشرة

💰 التكلفة: 10 توكن""",
                "tokens_deducted": 0
            }
        
        try:
            # تحليل المدخل
            parts = user_input.split()
            
            if len(parts) < 2:
                return {
                    "status": "error",
                    "output": "❌ صيغة خاطئة. استخدم: `/chart [type] [data] [labels]`",
                    "tokens_deducted": 0
                }
            
            chart_type = parts[0].lower()
            data = parts[1]
            labels = parts[2] if len(parts) > 2 else ""
            
            # تحويل نوع الرسم
            type_map = {
                "pie": "p3",
                "bar": "bvs",
                "line": "lc",
                "radar": "r"
            }
            
            cht = type_map.get(chart_type, "p3")
            
            # بناء URL
            base_url = "https://image-charts.com/chart"
            params = {
                "cht": cht,
                "chs": "700x400",
                "chd": f"t:{data}",
            }
            
            if labels:
                params["chl"] = labels
            
            # إضافة ألوان جميلة
            if chart_type == "pie":
                params["chf"] = "ps0-0,lg,45,ffeb3b,0.2,f44336,1|ps0-1,lg,45,8bc34a,0.2,009688,1"
            elif chart_type == "bar":
                params["chco"] = "4285F4,EA4335,FBBC04,34A853"
            elif chart_type == "line":
                params["chco"] = "4285F4"
                params["chm"] = "o,4285F4,0,-1,10"
            
            # بناء URL النهائي
            chart_url = f"{base_url}?{urllib.parse.urlencode(params)}"
            
            output = f"""📊 **تم إنشاء الرسم البياني!**

**النوع:** {chart_type.upper()}
**البيانات:** {data}
{f"**التسميات:** {labels}" if labels else ""}

**الرسم البياني:**
![Chart]({chart_url})

**الرابط المباشر:**
{chart_url}

---
💡 يمكنك تعديل الرابط لتخصيص الرسم أكثر"""
            
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
