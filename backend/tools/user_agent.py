"""
User Agent Parser Tool - محلل User Agent
"""
import httpx
from typing import Dict, Any
from .base import BaseTool


class UserAgentTool(BaseTool):
    """
    أداة تحليل User Agent
    """
    @property
    def name(self) -> str:
        return "/useragent"
    
    @property
    def description(self) -> str:
        return "🖥️ User Agent - تحليل معلومات المتصفح"
    
    @property
    def cost(self) -> int:
        return 10
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        تحليل User Agent string
        """
        
        if not user_input or not user_input.strip():
            return {
                "status": "success",
                "output": """🖥️ **User Agent Parser**

**الاستخدام:**
`/useragent [user_agent_string]`

**مثال:**
```
/useragent Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
```

**المعلومات المتاحة:**
✅ نوع المتصفح
✅ نظام التشغيل
✅ الجهاز
✅ الإصدارات

💰 التكلفة: 10 توكن""",
                "tokens_deducted": 0
            }
        
        try:
            ua_string = user_input.strip()
            
            # استخدام useragent API
            url = "https://api.apicagent.com/"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    url,
                    json={"ua": ua_string}
                )
                response.raise_for_status()
                data = response.json()
            
            browser_name = data.get("browser", {}).get("name", "Unknown")
            browser_version = data.get("browser", {}).get("version", "")
            
            os_name = data.get("os", {}).get("name", "Unknown")
            os_version = data.get("os", {}).get("version", "")
            
            device_type = data.get("device", {}).get("type", "Unknown")
            device_brand = data.get("device", {}).get("brand", "")
            device_model = data.get("device", {}).get("model", "")
            
            engine_name = data.get("engine", {}).get("name", "Unknown")
            engine_version = data.get("engine", {}).get("version", "")
            
            output = f"""🖥️ **User Agent Analysis**

**Browser:**
🌐 {browser_name} {browser_version}

**Operating System:**
💻 {os_name} {os_version}

**Device:**
📱 {device_type}"""
            
            if device_brand or device_model:
                output += f"\n🏷️ {device_brand} {device_model}".strip()
            
            output += f"""

**Rendering Engine:**
⚙️ {engine_name} {engine_version}

**Original UA:**
```
{ua_string[:100]}{"..." if len(ua_string) > 100 else ""}
```

---
🔍 Powered by apicagent.com"""
            
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
