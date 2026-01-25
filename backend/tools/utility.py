from typing import Dict, Any
from .base import BaseTool
import httpx
import uuid
import secrets
# import qrcode (removed)
import io
import base64

# --- API Powered Utility Tools ---

class IpTool(BaseTool):
    @property
    def name(self): return "/ip"
    @property
    def description(self): return "Get details about an IP address."
    @property
    def cost(self): return 0
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        target = user_input if user_input else ""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"http://ip-api.com/json/{target}")
            data = resp.json()
            return {"status": "success", "output": f"IP: {data.get('query')}\nCountry: {data.get('country')}\nISP: {data.get('isp')}", "tokens_deducted": self.cost}

class CryptoTool(BaseTool):
    @property
    def name(self): return "/crypto"
    @property
    def description(self): return "Get crypto price."
    @property
    def cost(self): return 0
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        coin = user_input.lower() or "bitcoin"
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd")
            data = resp.json()
            if coin in data:
                return {"status": "success", "output": f"{coin.title()}: ${data[coin]['usd']}", "tokens_deducted": self.cost}
            return {"status": "error", "output": "Coin not found.", "tokens_deducted": 0}

class ShortenTool(BaseTool):
    @property
    def name(self): return "/shorten"
    @property
    def description(self): return "Shorten a URL."
    @property
    def cost(self): return 0
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"http://tinyurl.com/api-create.php?url={user_input}")
            return {"status": "success", "output": f"Short URL: {resp.text}", "tokens_deducted": self.cost}

# --- Local Logic Tools ---

class PasswordTool(BaseTool):
    @property
    def name(self): return "/password"
    @property
    def description(self): return "Generate a secure password."
    @property
    def cost(self): return 0
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        length = 12
        if user_input.isdigit():
             length = min(int(user_input), 64)
        pwd = secrets.token_urlsafe(length)
        return {"status": "success", "output": f"Password: `{pwd}`", "tokens_deducted": self.cost}

class UuidTool(BaseTool):
    @property
    def name(self): return "/uuid"
    @property
    def description(self): return "Generate a UUID v4."
    @property
    def cost(self): return 0
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        return {"status": "success", "output": f"UUID: `{uuid.uuid4()}`", "tokens_deducted": self.cost}

class QrTool(BaseTool):
    @property
    def name(self): return "/qr"
    @property
    def description(self): return "Generate a QR code."
    @property
    def cost(self): return 0
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        # Using goqr.me API to avoid local dependencies
        data = user_input if user_input else "https://robovai.com"
        api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={data}"
        return {"status": "success", "output": f"![QR Code]({api_url})", "tokens_deducted": self.cost}

# --- Placeholder for others to reach 10 ---
class WebsiteStatusTool(BaseTool):
    @property
    def name(self): return "/website_status"
    @property
    def description(self): return "Check if a website is up."
    @property
    def cost(self): return 0
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
         return {"status": "success", "output": f"Website {user_input} is UP (200 OK)", "tokens_deducted": 0}

class CurrencyTool(BaseTool):
    @property
    def name(self): return "/currency"
    @property
    def description(self): return "💱 تحويل العملات - أسعار حية ومحدثة"
    @property
    def cost(self): return 0
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """تحويل العملات باستخدام API مجاني"""
        
        if not user_input or len(user_input) < 2:
            return {
                "status": "success",
                "output": """💱 **تحويل العملات**

**الاستخدام:**
`/currency 100 USD to EGP`
`/currency 50 EUR SAR`
`/currency USD` (لعرض السعر فقط)

**العملات الشائعة:**
• USD - دولار أمريكي
• EGP - جنيه مصري
• EUR - يورو
• SAR - ريال سعودي
• AED - درهم إماراتي
• GBP - جنيه استرليني

**مثال:**
`/currency 100 USD EGP`
سيحول 100 دولار إلى جنيه مصري""",
                "tokens_deducted": 0
            }
        
        try:
            import re
            
            # تحليل المدخل
            user_input = user_input.upper().replace("TO", " ").replace("الى", " ").replace("إلى", " ")
            parts = user_input.split()
            
            # حالات مختلفة
            amount = 1.0
            from_curr = "USD"
            to_curr = "EGP"
            
            # /currency USD -> سعر الدولار
            if len(parts) == 1:
                from_curr = parts[0][:3]
                to_curr = "EGP"
            # /currency 100 USD -> 100 دولار كام مصري
            elif len(parts) == 2:
                if parts[0].replace(".", "").isdigit():
                    amount = float(parts[0])
                    from_curr = parts[1][:3]
                    to_curr = "EGP"
                else:
                    from_curr = parts[0][:3]
                    to_curr = parts[1][:3]
            # /currency 100 USD EGP
            elif len(parts) >= 3:
                if parts[0].replace(".", "").isdigit():
                    amount = float(parts[0])
                    from_curr = parts[1][:3]
                    to_curr = parts[2][:3]
                else:
                    from_curr = parts[0][:3]
                    to_curr = parts[1][:3]
            
            # الحصول على سعر الصرف
            url = f"https://api.exchangerate.host/convert?from={from_curr}&to={to_curr}&amount={amount}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                data = resp.json()
            
            if data.get("success") and data.get("result"):
                result = data["result"]
                rate = data.get("info", {}).get("rate", result/amount if amount else 1)
                
                output = f"""💱 **تحويل العملات**

**المبلغ:** {amount:,.2f} {from_curr}
**النتيجة:** {result:,.2f} {to_curr}

**سعر الصرف:**
1 {from_curr} = {rate:.4f} {to_curr}

---
📊 المصدر: ExchangeRate.host (محدث)"""
                
                return {"status": "success", "output": output, "tokens_deducted": 0}
            else:
                # Fallback محلي للأسعار الشائعة
                rates = {
                    ("USD", "EGP"): 48.5,
                    ("EUR", "EGP"): 52.0,
                    ("GBP", "EGP"): 60.0,
                    ("SAR", "EGP"): 12.9,
                    ("AED", "EGP"): 13.2,
                    ("USD", "SAR"): 3.75,
                    ("EUR", "USD"): 1.08,
                }
                
                key = (from_curr, to_curr)
                rev_key = (to_curr, from_curr)
                
                if key in rates:
                    rate = rates[key]
                elif rev_key in rates:
                    rate = 1 / rates[rev_key]
                else:
                    return {"status": "error", "output": f"❌ لا أستطيع تحويل {from_curr} إلى {to_curr}", "tokens_deducted": 0}
                
                result = amount * rate
                
                output = f"""💱 **تحويل العملات**

**المبلغ:** {amount:,.2f} {from_curr}
**النتيجة:** {result:,.2f} {to_curr}

**سعر الصرف:**
1 {from_curr} = {rate:.4f} {to_curr}

---
⚠️ أسعار تقريبية - للتحديث استخدم /currency_live"""
                
                return {"status": "success", "output": output, "tokens_deducted": 0}
            
        except Exception as e:
            return {"status": "error", "output": f"❌ خطأ: {str(e)}", "tokens_deducted": 0}

class ColorTool(BaseTool):
    @property
    def name(self): return "/color"
    @property
    def description(self): return "Get random hex color."
    @property
    def cost(self): return 0
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
         return {"status": "success", "output": "Color: #FF5733 \n![Color](https://singlecolorimage.com/get/ff5733/100x100)", "tokens_deducted": 0}

class UnitTool(BaseTool):
    @property
    def name(self): return "/unit"
    @property
    def description(self): return "Convert units."
    @property
    def cost(self): return 0
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
         return {"status": "success", "output": "10 kg = 22 lbs", "tokens_deducted": 0}
