"""
Advice Slip Tool - نصائح عشوائية
"""
import httpx
from typing import Dict, Any
from .base import BaseTool


class AdviceSlipTool(BaseTool):
    """
    أداة النصائح العشوائية
    """
    @property
    def name(self) -> str:
        return "/advice"
    
    @property
    def description(self) -> str:
        return "💭 نصيحة - نصائح حياتية مفيدة"
    
    @property
    def cost(self) -> int:
        return 5
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        الحصول على نصيحة عشوائية
        """
        
        try:
            url = "https://api.adviceslip.com/advice"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            slip = data.get("slip", {})
            advice = slip.get("advice", "No advice available")
            advice_id = slip.get("id", "")
            
            output = f"""💭 **Random Advice #{advice_id}**

{advice}

---
🌟 Life wisdom from Advice Slip"""
            
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
