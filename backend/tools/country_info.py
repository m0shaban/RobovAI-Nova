"""
REST Countries Tool - معلومات الدول
"""
import httpx
from typing import Dict, Any
from .base import BaseTool


class CountryInfoTool(BaseTool):
    """
    أداة معلومات الدول
    """
    @property
    def name(self) -> str:
        return "/country"
    
    @property
    def description(self) -> str:
        return "🌍 معلومات الدول - معلومات شاملة عن أي دولة"
    
    @property
    def cost(self) -> int:
        return 10
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        الحصول على معلومات عن دولة
        """
        
        if not user_input or len(user_input) < 2:
            return {
                "status": "success",
                "output": """🌍 **معلومات الدول**

**الاستخدام:**
`/country [country name]`

**أمثلة:**
• `/country Egypt`
• `/country Saudi Arabia`
• `/country USA`

**المعلومات المتاحة:**
✅ العاصمة
✅ عدد السكان
✅ المساحة
✅ العملة
✅ اللغات
✅ العلم

💰 التكلفة: 10 توكن""",
                "tokens_deducted": 0
            }
        
        try:
            country_name = user_input.strip()
            url = f"https://restcountries.com/v3.1/name/{country_name}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            if not data or len(data) == 0:
                return {
                    "status": "error",
                    "output": f"❌ لم أجد معلومات عن: **{country_name}**",
                    "tokens_deducted": 0
                }
            
            country = data[0]
            
            name = country.get("name", {}).get("common", "N/A")
            capital = country.get("capital", ["N/A"])[0] if country.get("capital") else "N/A"
            population = country.get("population", 0)
            area = country.get("area", 0)
            region = country.get("region", "N/A")
            subregion = country.get("subregion", "N/A")
            
            # العملة
            currencies = country.get("currencies", {})
            currency_info = list(currencies.values())[0] if currencies else {}
            currency = f"{currency_info.get('name', 'N/A')} ({currency_info.get('symbol', '')})"
            
            # اللغات
            languages = country.get("languages", {})
            langs = ", ".join(languages.values()) if languages else "N/A"
            
            # العلم
            flag_url = country.get("flags", {}).get("png", "")
            
            output = f"""🌍 **{name}**

**العاصمة:** {capital}
**المنطقة:** {region} - {subregion}

**الإحصائيات:**
👥 **السكان:** {population:,}
📏 **المساحة:** {area:,} km²

**المعلومات:**
💰 **العملة:** {currency}
🗣️ **اللغات:** {langs}

**العلم:**
![Flag]({flag_url})

---
🌐 Powered by REST Countries API"""
            
            return {
                "status": "success",
                "output": output,
                "tokens_deducted": self.cost
            }
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {
                    "status": "error",
                    "output": f"❌ الدولة **{user_input}** غير موجودة",
                    "tokens_deducted": 0
                }
            return {
                "status": "error",
                "output": f"❌ خطأ: {e.response.status_code}",
                "tokens_deducted": 0
            }
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ: {str(e)}",
                "tokens_deducted": 0
            }
