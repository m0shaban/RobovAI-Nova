"""
IP Geolocation Tool - موقع الـ IP
"""
import httpx
from typing import Dict, Any
from .base import BaseTool


class IPGeoTool(BaseTool):
    """
    أداة تحديد موقع الـ IP
    """
    @property
    def name(self) -> str:
        return "/ipgeo"
    
    @property
    def description(self) -> str:
        return "🌍 موقع IP - معلومات جغرافية عن أي IP"
    
    @property
    def cost(self) -> int:
        return 10
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        الحصول على معلومات جغرافية عن IP
        """
        
        if not user_input or not user_input.strip():
            return {
                "status": "success",
                "output": """🌍 **IP Geolocation**

**الاستخدام:**
`/ipgeo [ip_address]`
أو اتركه فارغاً لمعرفة موقعك الحالي

**أمثلة:**
• `/ipgeo` - موقعك الحالي
• `/ipgeo 8.8.8.8` - Google DNS
• `/ipgeo 1.1.1.1` - Cloudflare DNS

**المعلومات المتاحة:**
✅ الدولة والمدينة
✅ الإحداثيات
✅ المنطقة الزمنية
✅ مزود الخدمة (ISP)

💰 التكلفة: 10 توكن""",
                "tokens_deducted": 0
            }
        
        try:
            ip_address = user_input.strip()
            
            # استخدام ip-api.com (مجاني تماماً)
            url = f"http://ip-api.com/json/{ip_address}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            if data.get("status") == "fail":
                return {
                    "status": "error",
                    "output": f"❌ {data.get('message', 'Invalid IP address')}",
                    "tokens_deducted": 0
                }
            
            country = data.get("country", "N/A")
            country_code = data.get("countryCode", "")
            region = data.get("regionName", "N/A")
            city = data.get("city", "N/A")
            zip_code = data.get("zip", "N/A")
            lat = data.get("lat", 0)
            lon = data.get("lon", 0)
            timezone = data.get("timezone", "N/A")
            isp = data.get("isp", "N/A")
            org = data.get("org", "N/A")
            as_name = data.get("as", "N/A")
            query = data.get("query", ip_address)
            
            output = f"""🌍 **IP Geolocation: {query}**

**Location:**
🏳️ **Country:** {country} ({country_code})
🏙️ **City:** {city}, {region}
📮 **ZIP:** {zip_code}

**Coordinates:**
📍 **Lat/Lon:** {lat}, {lon}
🕐 **Timezone:** {timezone}

**Network:**
🌐 **ISP:** {isp}
🏢 **Organization:** {org}
🔢 **AS:** {as_name}

**Map:**
[View on Google Maps](https://www.google.com/maps?q={lat},{lon})

---
🌐 Powered by ip-api.com"""
            
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
