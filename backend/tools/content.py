from typing import Dict, Any
from .base import BaseTool
from backend.core.llm import llm_client


class SocialTool(BaseTool):
    @property
    def name(self) -> str:
        return "/social"

    @property
    def description(self) -> str:
        return "Generates viral posts in Egyptian/Arabic/English with hashtags."

    @property
    def cost(self) -> int:
        return 1

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"Act as a social media expert for the Egyptian market. Generate a viral post with hashtags for: {user_input}"
        output = await llm_client.generate(prompt, provider="auto")
        return {"status": "success", "output": output, "tokens_deducted": self.cost}


class ScriptTool(BaseTool):
    @property
    def name(self) -> str:
        return "/script"

    @property
    def description(self) -> str:
        return "Creates YouTube/TikTok video scripts."

    @property
    def cost(self) -> int:
        return 1

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"Create a video script for TikTok about: {user_input}. Include scene descriptions, dialogue, and timing."
        output = await llm_client.generate(prompt, provider="auto")
        return {"status": "success", "output": output, "tokens_deducted": self.cost}
