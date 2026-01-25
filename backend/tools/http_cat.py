"""
HTTP Cat Tool - صور قطط لأكواد HTTP
"""
from typing import Dict, Any
from .base import BaseTool


class HTTPCatTool(BaseTool):
    """
    أداة صور القطط لأكواد HTTP
    """
    @property
    def name(self) -> str:
        return "/httpcat"
    
    @property
    def description(self) -> str:
        return "🐱 HTTP Cat - صور قطط لأكواد HTTP"
    
    @property
    def cost(self) -> int:
        return 5
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        الحصول على صورة قطة لكود HTTP
        """
        
        if not user_input or not user_input.strip().isdigit():
            return {
                "status": "success",
                "output": """🐱 **HTTP Cat**

**الاستخدام:**
`/httpcat [status_code]`

**أمثلة:**
• `/httpcat 200` - OK
• `/httpcat 404` - Not Found
• `/httpcat 500` - Internal Server Error
• `/httpcat 418` - I'm a teapot

**أكواد شائعة:**
✅ 200, 201, 204
❌ 400, 401, 403, 404
⚠️ 500, 502, 503

💰 التكلفة: 5 توكن""",
                "tokens_deducted": 0
            }
        
        try:
            status_code = user_input.strip()
            image_url = f"https://http.cat/{status_code}"
            
            # قائمة الأكواد الشائعة
            status_messages = {
                "200": "OK",
                "201": "Created",
                "204": "No Content",
                "400": "Bad Request",
                "401": "Unauthorized",
                "403": "Forbidden",
                "404": "Not Found",
                "418": "I'm a teapot",
                "500": "Internal Server Error",
                "502": "Bad Gateway",
                "503": "Service Unavailable"
            }
            
            message = status_messages.get(status_code, "HTTP Status Code")
            
            output = f"""🐱 **HTTP {status_code} - {message}**

![HTTP Cat]({image_url})

**Image URL:**
{image_url}

---
😸 Powered by HTTP.cat"""
            
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
