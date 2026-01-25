from typing import Dict, Any
from .base import BaseTool
import urllib.parse

class ImagineTool(BaseTool):
    @property
    def name(self) -> str:
        return "/imagine"

    @property
    def description(self) -> str:
        return "Directly calls Pollinations AI to return high-quality images."

    @property
    def cost(self) -> int:
        return 5  # Higher cost

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        # Pollinations AI URL construction
        encoded_prompt = urllib.parse.quote(user_input)
        image_url = f"https://pollinations.ai/p/{encoded_prompt}"
        
        return {
            "status": "success",
            "output": f"![Generated Image]({image_url})",
            "tokens_deducted": self.cost
        }
