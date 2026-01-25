"""
Chuck Norris Jokes Tool - نكت Chuck Norris
"""
import httpx
from typing import Dict, Any
from .base import BaseTool


class ChuckNorrisTool(BaseTool):
    """
    أداة نكت Chuck Norris
    """
    @property
    def name(self) -> str:
        return "/chuck"
    
    @property
    def description(self) -> str:
        return "😂 نكت Chuck Norris - نكت مضحكة عشوائية"
    
    @property
    def cost(self) -> int:
        return 5
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        الحصول على نكتة Chuck Norris عشوائية
        """
        
        try:
            url = "https://api.chucknorris.io/jokes/random"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            joke = data.get("value", "No joke available")
            
            output = f"""😂 **Chuck Norris Joke**

{joke}

---
💡 Powered by chucknorris.io"""
            
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
