from typing import Dict, Any
from .base import BaseTool
from backend.core.llm import llm_client
from backend.core.config import settings

# --- Social & Content ---


class SocialTool(BaseTool):
    @property
    def name(self):
        return "/social"

    @property
    def description(self):
        return "Viral social post."

    @property
    def cost(self):
        return 1

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"Create a viral social media post about: {user_input}"
        output = await llm_client.generate(
            prompt, provider="nvidia", model=settings.NVIDIA_WRITING_MODEL
        )
        return {"status": "success", "output": output, "tokens_deducted": self.cost}


class ScriptTool(BaseTool):
    @property
    def name(self):
        return "/script"

    @property
    def description(self):
        return "Write a video script."

    @property
    def cost(self):
        return 1

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"Write a video script for: {user_input}"
        output = await llm_client.generate(
            prompt, provider="nvidia", model=settings.NVIDIA_WRITING_MODEL
        )
        return {"status": "success", "output": output, "tokens_deducted": self.cost}


class EmailFormalTool(BaseTool):
    @property
    def name(self):
        return "/email_formal"

    @property
    def description(self):
        return "Make email professional."

    @property
    def cost(self):
        return 1

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        output = await llm_client.generate(
            f"Rewrite professionally: {user_input}", provider="auto"
        )
        return {"status": "success", "output": output, "tokens_deducted": self.cost}


class EmailAngryTool(BaseTool):
    @property
    def name(self):
        return "/email_angry"

    @property
    def description(self):
        return "Make email stern/angry (professional)."

    @property
    def cost(self):
        return 1

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        output = await llm_client.generate(
            f"Rewrite powerfully/sternly: {user_input}", provider="auto"
        )
        return {"status": "success", "output": output, "tokens_deducted": self.cost}


# --- Education ---


class Eli5Tool(BaseTool):
    @property
    def name(self):
        return "/eli5"

    @property
    def description(self):
        return "Explain like I'm 5."

    @property
    def cost(self):
        return 1

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        output = await llm_client.generate(f"ELI5: {user_input}", provider="auto")
        return {"status": "success", "output": output, "tokens_deducted": self.cost}


class QuizTool(BaseTool):
    @property
    def name(self):
        return "/quiz"

    @property
    def description(self):
        return "Generate a quiz."

    @property
    def cost(self):
        return 1

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        output = await llm_client.generate(
            f"Create a 3 question quiz about: {user_input}", provider="auto"
        )
        return {"status": "success", "output": output, "tokens_deducted": self.cost}


class BookRecTool(BaseTool):
    @property
    def name(self):
        return "/book_rec"

    @property
    def description(self):
        return "Book recommendation."

    @property
    def cost(self):
        return 1

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        output = await llm_client.generate(
            f"Recommend books similar to: {user_input}", provider="auto"
        )
        return {"status": "success", "output": output, "tokens_deducted": self.cost}


class TranslateEgyTool(BaseTool):
    @property
    def name(self):
        return "/translate_egy"

    @property
    def description(self):
        return "Translate to Egyptian Arabic."

    @property
    def cost(self):
        return 1

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        output = await llm_client.generate(
            f"Translate to Egyptian Slang: {user_input}", provider="auto"
        )
        return {"status": "success", "output": output, "tokens_deducted": self.cost}


class GrammarTool(BaseTool):
    @property
    def name(self):
        return "/grammar"

    @property
    def description(self):
        return "Fix grammar."

    @property
    def cost(self):
        return 1

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        output = await llm_client.generate(
            f"Fix grammar: {user_input}", provider="auto"
        )
        return {"status": "success", "output": output, "tokens_deducted": self.cost}


class SynonymTool(BaseTool):
    @property
    def name(self):
        return "/synonym"

    @property
    def description(self):
        return "Get synonyms."

    @property
    def cost(self):
        return 0  # Cheap enough to be free or logic based

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        output = await llm_client.generate(
            f"List synonyms for: {user_input}", provider="auto"
        )
        return {"status": "success", "output": output, "tokens_deducted": self.cost}
