"""
Enhanced Currency Tool - تحويل العملات المحسّن
"""
import os
import httpx
from typing import Dict, Any
from .base import BaseTool


class CurrencyEnhancedTool(BaseTool):
    """
    أداة تحويل العملات المحسّنة باستخدام ExchangeRate-API
    """
    @property
    def name(self) -> str:
        return "/currency_live"
    
    @property
    def description(self) -> str:
        return "💱 تحويل العملات المباشر - أسعار حية ودقيقة من ExchangeRate-API"
    
    @property
    def cost(self) -> int:
        return 15
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        تحويل العملات بأسعار حية
        """
        
        if not user_input or len(user_input) < 3:
            return {
                "status": "success",
                "output": """💱 **تحويل العملات المباشر**

**الاستخدام:**
`/currency_live [amount] [from] to [to]`

**أمثلة:**
• `/currency_live 100 USD to EGP`
• `/currency_live 50 EUR to SAR`
• `/currency_live 1000 EGP to USD`

**المميزات:**
✅ أسعار صرف حية ومحدثة
✅ دعم +150 عملة
✅ دقة عالية
✅ معدلات التحديث كل ساعة

💰 التكلفة: 15 توكن""",
                "tokens_deducted": 0
            }
        
        # التحقق من API Key
        api_key = os.getenv("EXCHANGERATE_API_KEY")
        if not api_key:
            return {
                "status": "error",
                "output": "❌ مفتاح API غير موجود في ملف .env\n\nأضف: EXCHANGERATE_API_KEY=your_key",
                "tokens_deducted": 0
            }
        
        try:
            # تحليل المدخل
            parts = user_input.upper().replace("TO", " ").split()
            
            if len(parts) < 3:
                return {
                    "status": "error",
                    "output": "❌ صيغة خاطئة. استخدم: `/currency_live [amount] [from] to [to]`",
                    "tokens_deducted": 0
                }
            
            amount = float(parts[0])
            from_currency = parts[1]
            to_currency = parts[2]
            
            # الحصول على سعر الصرف
            url = f"https://v6.exchangerate-api.com/v6/{api_key}/pair/{from_currency}/{to_currency}/{amount}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            if data.get("result") != "success":
                return {
                    "status": "error",
                    "output": f"❌ خطأ: {data.get('error-type', 'Unknown error')}",
                    "tokens_deducted": 0
                }
            
            conversion_rate = data.get("conversion_rate")
            conversion_result = data.get("conversion_result")
            
            output = f"""💱 **تحويل العملات**

**المبلغ الأصلي:** {amount:,.2f} {from_currency}
**النتيجة:** {conversion_result:,.2f} {to_currency}

**سعر الصرف:** 1 {from_currency} = {conversion_rate:.4f} {to_currency}

**آخر تحديث:** {data.get('time_last_update_utc', 'N/A')}

---
💡 الأسعار محدثة كل ساعة من ExchangeRate-API"""
            
            return {
                "status": "success",
                "output": output,
                "tokens_deducted": self.cost
            }
            
        except ValueError:
            return {
                "status": "error",
                "output": "❌ المبلغ يجب أن يكون رقماً صحيحاً",
                "tokens_deducted": 0
            }
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ: {str(e)}",
                "tokens_deducted": 0
            }
