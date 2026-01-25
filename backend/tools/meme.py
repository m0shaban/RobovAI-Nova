"""
Meme Generator Tool - مولد الميمز
"""
import httpx
from typing import Dict, Any
from .base import BaseTool


class MemeTool(BaseTool):
    """
    أداة الميمز العشوائية
    """
    @property
    def name(self) -> str:
        return "/meme"
    
    @property
    def description(self) -> str:
        return "😂 ميم عشوائي - ميمز مضحكة من Reddit"
    
    @property
    def cost(self) -> int:
        return 5
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        الحصول على ميم عشوائي
        """
        
        try:
            url = "https://meme-api.com/gimme"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            title = data.get("title", "Meme")
            image_url = data.get("url", "")
            subreddit = data.get("subreddit", "memes")
            author = data.get("author", "unknown")
            post_link = data.get("postLink", "")
            upvotes = data.get("ups", 0)
            
            output = f"""😂 **{title}**

![Meme]({image_url})

**Subreddit:** r/{subreddit}
**Author:** u/{author}
**Upvotes:** {upvotes:,} ⬆️

**Source:**
{post_link}

---
😂 Powered by Meme API"""
            
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
