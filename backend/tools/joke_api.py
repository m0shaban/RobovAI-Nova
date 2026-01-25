"""
JokeAPI Tool - نكت متنوعة
"""
import httpx
from typing import Dict, Any
from .base import BaseTool


class JokeAPITool(BaseTool):
    """
    أداة النكت المتنوعة
    """
    @property
    def name(self) -> str:
        return "/joke"
    
    @property
    def description(self) -> str:
        return "😄 نكتة - نكت متنوعة ومضحكة"
    
    @property
    def cost(self) -> int:
        return 5
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        الحصول على نكتة عشوائية
        """
        
        try:
            # استخدام JokeAPI مع تصفية المحتوى غير اللائق
            url = "https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,religious,political,racist,sexist,explicit"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            if data.get("error"):
                return {
                    "status": "error",
                    "output": "❌ فشل في الحصول على نكتة",
                    "tokens_deducted": 0
                }
            
            joke_type = data.get("type")
            category = data.get("category", "General")
            
            if joke_type == "single":
                joke_text = data.get("joke", "")
                output = f"""😄 **Joke - {category}**

{joke_text}

---
😂 Powered by JokeAPI"""
            else:
                setup = data.get("setup", "")
                delivery = data.get("delivery", "")
                output = f"""😄 **Joke - {category}**

{setup}

**Punchline:**
||{delivery}||

---
😂 Powered by JokeAPI"""
            
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
