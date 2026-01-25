"""
Advanced Calculator Tool - حاسبة متقدمة
"""
import httpx
from typing import Dict, Any
from .base import BaseTool


class AdvancedCalculatorTool(BaseTool):
    """
    أداة الحاسبة المتقدمة باستخدام FastAPI Calculator
    """
    @property
    def name(self) -> str:
        return "/calc_advanced"
    
    @property
    def description(self) -> str:
        return "🧮 حاسبة متقدمة - عمليات رياضية، مثلثات، إحصائيات"
    
    @property
    def cost(self) -> int:
        return 10
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        إجراء عمليات حسابية متقدمة
        """
        
        if not user_input or len(user_input) < 1:
            return {
                "status": "success",
                "output": """🧮 **الحاسبة المتقدمة**

**الاستخدام:**
`/calc_advanced [expression]`

**العمليات الأساسية:**
• `/calc_advanced 2 + 2`
• `/calc_advanced 10 * 5`
• `/calc_advanced 100 / 4`
• `/calc_advanced 2 ^ 3` (قوة)

**الدوال المتقدمة:**
• `/calc_advanced sqrt(16)` - جذر تربيعي
• `/calc_advanced sin(30)` - جيب الزاوية
• `/calc_advanced cos(45)` - جيب التمام
• `/calc_advanced log(100)` - لوغاريتم

**المميزات:**
✅ عمليات حسابية أساسية
✅ دوال رياضية متقدمة
✅ دوال مثلثية
✅ لوغاريتمات وجذور

💰 التكلفة: 10 توكن""",
                "tokens_deducted": 0
            }
        
        try:
            expression = user_input.strip()
            
            # استخدام FastAPI Calculator
            base_url = "https://fastapi-calculadora.onrender.com"
            
            # تحديد نوع العملية
            if "sqrt" in expression.lower():
                # جذر تربيعي
                num = expression.lower().replace("sqrt", "").replace("(", "").replace(")", "").strip()
                url = f"{base_url}/raiz-cuadrada/{num}"
            elif "sin" in expression.lower():
                # جيب
                angle = expression.lower().replace("sin", "").replace("(", "").replace(")", "").strip()
                url = f"{base_url}/seno/{angle}"
            elif "cos" in expression.lower():
                # جيب التمام
                angle = expression.lower().replace("cos", "").replace("(", "").replace(")", "").strip()
                url = f"{base_url}/coseno/{angle}"
            elif "tan" in expression.lower():
                # ظل
                angle = expression.lower().replace("tan", "").replace("(", "").replace(")", "").strip()
                url = f"{base_url}/tangente/{angle}"
            elif "log" in expression.lower():
                # لوغاريتم
                num = expression.lower().replace("log", "").replace("(", "").replace(")", "").strip()
                url = f"{base_url}/logaritmo/{num}"
            elif "^" in expression or "**" in expression:
                # قوة
                parts = expression.replace("^", "**").split("**")
                if len(parts) == 2:
                    base = parts[0].strip()
                    exp = parts[1].strip()
                    url = f"{base_url}/potencia/{base}/{exp}"
                else:
                    return {
                        "status": "error",
                        "output": "❌ صيغة خاطئة للقوة. استخدم: `base ^ exponent`",
                        "tokens_deducted": 0
                    }
            else:
                # عمليات أساسية
                # تحويل العملية لصيغة URL
                if "+" in expression:
                    parts = expression.split("+")
                    url = f"{base_url}/suma/{parts[0].strip()}/{parts[1].strip()}"
                elif "-" in expression:
                    parts = expression.split("-")
                    url = f"{base_url}/resta/{parts[0].strip()}/{parts[1].strip()}"
                elif "*" in expression or "×" in expression:
                    parts = expression.replace("×", "*").split("*")
                    url = f"{base_url}/multiplicacion/{parts[0].strip()}/{parts[1].strip()}"
                elif "/" in expression or "÷" in expression:
                    parts = expression.replace("÷", "/").split("/")
                    url = f"{base_url}/division/{parts[0].strip()}/{parts[1].strip()}"
                else:
                    return {
                        "status": "error",
                        "output": "❌ عملية غير مدعومة. استخدم: +, -, *, /, ^, sqrt, sin, cos, tan, log",
                        "tokens_deducted": 0
                    }
            
            # إجراء الطلب
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            result = data.get("resultado", data.get("result", "N/A"))
            
            output = f"""🧮 **نتيجة الحساب**

**العملية:** `{expression}`
**النتيجة:** `{result}`

---
💡 Powered by FastAPI Calculator"""
            
            return {
                "status": "success",
                "output": output,
                "tokens_deducted": self.cost
            }
            
        except httpx.HTTPStatusError as e:
            return {
                "status": "error",
                "output": f"❌ خطأ من API: {e.response.status_code}",
                "tokens_deducted": 0
            }
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ: {str(e)}",
                "tokens_deducted": 0
            }
