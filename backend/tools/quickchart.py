"""
QuickChart Tool - رسوم بيانية متقدمة باستخدام Chart.js
"""
import urllib.parse
import json
from typing import Dict, Any
from .base import BaseTool


class QuickChartTool(BaseTool):
    """
    أداة إنشاء رسوم بيانية متقدمة باستخدام QuickChart و Chart.js
    """
    @property
    def name(self) -> str:
        return "/quickchart"
    
    @property
    def description(self) -> str:
        return "📈 QuickChart - رسوم بيانية متقدمة بـ Chart.js (bar, line, pie, doughnut)"
    
    @property
    def cost(self) -> int:
        return 15
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        إنشاء رسم بياني متقدم
        """
        
        if not user_input or len(user_input) < 3:
            return {
                "status": "success",
                "output": """📈 **QuickChart - رسوم بيانية متقدمة**

**الاستخدام:**
`/quickchart [type] [data] [labels]`

**الأنواع:**
• `bar` - أعمدة
• `line` - خطي
• `pie` - دائري
• `doughnut` - دونات
• `radar` - راداري

**أمثلة:**
• `/quickchart bar 30,60,90 Jan|Feb|Mar`
• `/quickchart line 10,20,30,25 Q1|Q2|Q3|Q4`
• `/quickchart pie 40,30,30 Sales|Marketing|Dev`

**المميزات:**
✅ رسوم احترافية بـ Chart.js
✅ ألوان تلقائية جميلة
✅ دعم رسوم معقدة
✅ جودة عالية

💰 التكلفة: 15 توكن""",
                "tokens_deducted": 0
            }
        
        try:
            # تحليل المدخل
            parts = user_input.split()
            
            if len(parts) < 2:
                return {
                    "status": "error",
                    "output": "❌ صيغة خاطئة. استخدم: `/quickchart [type] [data] [labels]`",
                    "tokens_deducted": 0
                }
            
            chart_type = parts[0].lower()
            data_str = parts[1]
            labels_str = parts[2] if len(parts) > 2 else ""
            
            # تحويل البيانات
            data_values = [int(x) for x in data_str.split(',')]
            labels = labels_str.split('|') if labels_str else [f"Item {i+1}" for i in range(len(data_values))]
            
            # بناء Chart.js config
            chart_config = {
                "type": chart_type,
                "data": {
                    "labels": labels,
                    "datasets": [{
                        "label": "Data",
                        "data": data_values
                    }]
                }
            }
            
            # إضافة ألوان جميلة
            if chart_type in ["pie", "doughnut"]:
                chart_config["data"]["datasets"][0]["backgroundColor"] = [
                    "rgb(255, 99, 132)",
                    "rgb(54, 162, 235)",
                    "rgb(255, 205, 86)",
                    "rgb(75, 192, 192)",
                    "rgb(153, 102, 255)",
                    "rgb(255, 159, 64)"
                ]
            elif chart_type == "bar":
                chart_config["data"]["datasets"][0]["backgroundColor"] = "rgb(54, 162, 235)"
            elif chart_type == "line":
                chart_config["data"]["datasets"][0]["borderColor"] = "rgb(54, 162, 235)"
                chart_config["data"]["datasets"][0]["fill"] = False
            
            # إضافة عنوان
            chart_config["options"] = {
                "title": {
                    "display": True,
                    "text": f"{chart_type.upper()} Chart"
                }
            }
            
            # تحويل لـ JSON وترميز
            config_json = json.dumps(chart_config)
            encoded_config = urllib.parse.quote(config_json)
            
            # بناء URL
            chart_url = f"https://quickchart.io/chart?c={encoded_config}&width=600&height=400"
            
            output = f"""📈 **تم إنشاء الرسم البياني!**

**النوع:** {chart_type.upper()}
**البيانات:** {data_str}
**التسميات:** {', '.join(labels)}

**الرسم البياني:**
![Chart]({chart_url})

**الرابط المباشر:**
{chart_url}

---
💡 مدعوم بـ Chart.js - أكثر مكتبة رسوم شعبية!
🎨 يمكنك تخصيص الألوان والأنماط أكثر"""
            
            return {
                "status": "success",
                "output": output,
                "tokens_deducted": self.cost
            }
            
        except ValueError:
            return {
                "status": "error",
                "output": "❌ البيانات يجب أن تكون أرقاماً مفصولة بفواصل (مثال: 10,20,30)",
                "tokens_deducted": 0
            }
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ: {str(e)}",
                "tokens_deducted": 0
            }
