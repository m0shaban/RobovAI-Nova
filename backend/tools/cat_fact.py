"""
Cat Facts Tool - حقائق عن القطط
"""
import httpx
from typing import Dict, Any
from .base import BaseTool


class CatFactTool(BaseTool):
    """
    أداة حقائق القطط
    """
    @property
    def name(self) -> str:
        return "/catfact"
    
    @property
    def description(self) -> str:
        return "🐱 حقيقة عن القطط - معلومات مثيرة عن القطط"
    
    @property
    def cost(self) -> int:
        return 5
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        الحصول على حقيقة عن القطط
        """
        
        try:
            url = "https://catfact.ninja/fact"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            fact = data.get("fact", "No fact available")
            
            output = f"""🐱 **Cat Fact**

{fact}

---
😺 Meow! Learn more about cats!"""
            
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
