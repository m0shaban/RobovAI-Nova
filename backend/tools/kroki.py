"""
Kroki Diagrams Tool - إنشاء المخططات التقنية
"""
import urllib.parse
import base64
import zlib
from typing import Dict, Any
from .base import BaseTool


class KrokiTool(BaseTool):
    """
    أداة إنشاء المخططات التقنية باستخدام Kroki
    """
    @property
    def name(self) -> str:
        return "/diagram"
    
    @property
    def description(self) -> str:
        return "🎨 إنشاء مخططات تقنية - UML, flowcharts, sequence diagrams"
    
    @property
    def cost(self) -> int:
        return 15
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        إنشاء مخطط تقني
        """
        
        if not user_input or len(user_input) < 3:
            return {
                "status": "success",
                "output": """🎨 **إنشاء المخططات التقنية**

**الاستخدام:**
`/diagram [type] [code]`

**الأنواع المدعومة:**
• `flowchart` - مخطط انسيابي
• `sequence` - تسلسل العمليات
• `class` - مخطط الكلاسات
• `er` - علاقات الكيانات

**أمثلة:**

**Flowchart:**
```
/diagram flowchart
graph TD
A[Start] --> B[Process]
B --> C[End]
```

**Sequence:**
```
/diagram sequence
Alice->Bob: Hello
Bob->Alice: Hi!
```

**المميزات:**
✅ مخططات احترافية
✅ دعم 20+ نوع
✅ مجاني بالكامل
✅ جودة عالية

💰 التكلفة: 15 توكن""",
                "tokens_deducted": 0
            }
        
        try:
            # تحليل المدخل
            lines = user_input.strip().split('\n')
            diagram_type = lines[0].lower().strip()
            
            # إزالة السطر الأول (نوع المخطط) من الكود
            diagram_code = '\n'.join(lines[1:]).strip() if len(lines) > 1 else user_input
            
            # تحديد نوع Kroki
            type_map = {
                "flowchart": "graphviz",
                "flow": "graphviz",
                "sequence": "plantuml",
                "seq": "plantuml",
                "class": "plantuml",
                "er": "plantuml",
                "uml": "plantuml",
                "mermaid": "mermaid",
                "blockdiag": "blockdiag"
            }
            
            kroki_type = type_map.get(diagram_type, "graphviz")
            
            # تحويل الكود لتنسيق Kroki
            if kroki_type == "graphviz" and not diagram_code.startswith("digraph"):
                # إضافة wrapper لـ Graphviz
                diagram_code = f"digraph G {{\n{diagram_code}\n}}"
            elif kroki_type == "plantuml" and not diagram_code.startswith("@start"):
                # إضافة wrapper لـ PlantUML
                diagram_code = f"@startuml\n{diagram_code}\n@enduml"
            
            # ضغط وتشفير الكود
            compressed = zlib.compress(diagram_code.encode('utf-8'), 9)
            encoded = base64.urlsafe_b64encode(compressed).decode('utf-8')
            
            # بناء URL
            diagram_url = f"https://kroki.io/{kroki_type}/svg/{encoded}"
            
            output = f"""🎨 **تم إنشاء المخطط!**

**النوع:** {diagram_type.upper()}
**المحرك:** {kroki_type}

**المخطط:**
![Diagram]({diagram_url})

**الرابط المباشر:**
{diagram_url}

---
💡 يمكنك تعديل الكود وإعادة التوليد
🔗 Powered by Kroki.io"""
            
            return {
                "status": "success",
                "output": output,
                "tokens_deducted": self.cost
            }
            
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ: {str(e)}\n\n💡 تأكد من صحة كود المخطط",
                "tokens_deducted": 0
            }
