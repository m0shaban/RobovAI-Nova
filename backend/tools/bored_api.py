"""
Bored API Tool - اقتراحات أنشطة
"""
import httpx
from typing import Dict, Any
from .base import BaseTool


class BoredAPITool(BaseTool):
    """
    أداة اقتراحات الأنشطة
    """
    @property
    def name(self) -> str:
        return "/bored"
    
    @property
    def description(self) -> str:
        return "🎲 نشاط عشوائي - اقتراحات لأنشطة ممتعة"
    
    @property
    def cost(self) -> int:
        return 5
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        الحصول على اقتراح نشاط عشوائي
        """
        
        try:
            url = "https://www.boredapi.com/api/activity"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            activity = data.get("activity", "No activity found")
            activity_type = data.get("type", "").capitalize()
            participants = data.get("participants", 1)
            
            # رموز للأنواع المختلفة
            type_icons = {
                "Education": "📚",
                "Recreational": "🎮",
                "Social": "👥",
                "Diy": "🔨",
                "Charity": "❤️",
                "Cooking": "🍳",
                "Relaxation": "😌",
                "Music": "🎵",
                "Busywork": "📋"
            }
            
            icon = type_icons.get(activity_type, "🎲")
            
            output = f"""🎲 **Activity Suggestion**

{icon} **{activity}**

**Type:** {activity_type}
**Participants:** {participants} {"person" if participants == 1 else "people"}

---
💡 Feeling bored? Try this!"""
            
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
