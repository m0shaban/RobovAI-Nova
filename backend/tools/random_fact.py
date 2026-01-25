"""
Random Facts Tool - حقائق عشوائية (Fixed)
"""
import httpx
from typing import Dict, Any
from .base import BaseTool


class RandomFactTool(BaseTool):
    """
    أداة الحقائق العشوائية
    """
    @property
    def name(self) -> str:
        return "/fact"
    
    @property
    def description(self) -> str:
        return "💡 حقيقة عشوائية - حقائق مثيرة ومفيدة"
    
    @property
    def cost(self) -> int:
        return 5
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        الحصول على حقيقة عشوائية
        """
        
        try:
            # Updated URL (API v2)
            url = "https://uselessfacts.jsph.pl/api/v2/facts/random?language=en"
            
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            fact = data.get("text", "No fact available")
            source = data.get("source", "Unknown")
            
            output = f"""💡 **حقيقة عشوائية**

{fact}

📚 المصدر: {source}

---
🌟 هل كنت تعرف؟"""
            
            return {
                "status": "success",
                "output": output,
                "tokens_deducted": self.cost
            }
            
        except Exception as e:
            # Fallback to another API
            try:
                async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                    response = await client.get("https://api.api-ninjas.com/v1/facts?limit=1")
                    data = response.json()
                    if data and len(data) > 0:
                        fact = data[0].get("fact", "No fact available")
                        return {
                            "status": "success",
                            "output": f"💡 **حقيقة عشوائية**\n\n{fact}\n\n---\n🌟 هل كنت تعرف؟",
                            "tokens_deducted": self.cost
                        }
            except:
                pass
            
            return {
                "status": "error",
                "output": f"❌ خطأ: {str(e)}",
                "tokens_deducted": 0
            }
