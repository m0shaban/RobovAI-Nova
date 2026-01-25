"""
Random Dog Tool - صور كلاب عشوائية
"""
import httpx
from typing import Dict, Any
from .base import BaseTool


class RandomDogTool(BaseTool):
    """
    أداة صور الكلاب العشوائية
    """
    @property
    def name(self) -> str:
        return "/randomdog"
    
    @property
    def description(self) -> str:
        return "🐕 صورة كلب عشوائية - صور كلاب لطيفة"
    
    @property
    def cost(self) -> int:
        return 5
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        الحصول على صورة كلب عشوائية
        """
        
        try:
            url = "https://dog.ceo/api/breeds/image/random"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            if data.get("status") != "success":
                return {
                    "status": "error",
                    "output": "❌ فشل في الحصول على صورة",
                    "tokens_deducted": 0
                }
            
            image_url = data.get("message", "")
            
            output = f"""🐕 **Random Dog Image**

![Dog]({image_url})

**Image URL:**
{image_url}

---
🐾 Powered by Dog CEO API"""
            
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
