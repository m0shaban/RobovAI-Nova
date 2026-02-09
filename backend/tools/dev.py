from typing import Dict, Any
from .base import BaseTool
from backend.core.llm import llm_client
from backend.core.config import settings
import time
import hashlib

# --- NVIDIA Powered Coding Tools ---


class CodeFixTool(BaseTool):
    @property
    def name(self):
        return "/code_fix"

    @property
    def description(self):
        return "Debug and fix code."

    @property
    def cost(self):
        return 2  # Premium

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"Fix this code and explain the bug:\n```{user_input}```"
        # Using NVIDIA for better coding capabilities
        output = await llm_client.generate(
            prompt,
            provider="nvidia",
            system_prompt="You are a senior software engineer.",
            model=settings.NVIDIA_CODING_MODEL,
        )
        return {"status": "success", "output": output, "tokens_deducted": self.cost}


class SqlTool(BaseTool):
    @property
    def name(self):
        return "/sql"

    @property
    def description(self):
        return "Generate SQL query from text."

    @property
    def cost(self):
        return 1

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"Generate a SQL query for: {user_input}"
        output = await llm_client.generate(
            prompt,
            provider="nvidia",
            system_prompt="You are a SQL expert.",
            model=settings.NVIDIA_CODING_MODEL,
        )
        return {
            "status": "success",
            "output": f"```sql\n{output}\n```",
            "tokens_deducted": self.cost,
        }


class RegexTool(BaseTool):
    @property
    def name(self):
        return "/regex"

    @property
    def description(self):
        return "Generate Regex Pattern."

    @property
    def cost(self):
        return 1

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"Create a regex for: {user_input}"
        output = await llm_client.generate(
            prompt, provider="nvidia", model=settings.NVIDIA_CODING_MODEL
        )
        return {
            "status": "success",
            "output": f"`{output}`",
            "tokens_deducted": self.cost,
        }


class ExplainCodeTool(BaseTool):
    @property
    def name(self):
        return "/explain_code"

    @property
    def description(self):
        return "Explain complex code."

    @property
    def cost(self):
        return 1

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"Explain this code in simple terms:\n```{user_input}```"
        output = await llm_client.generate(
            prompt, provider="nvidia", model=settings.NVIDIA_CODING_MODEL
        )
        return {"status": "success", "output": output, "tokens_deducted": self.cost}


class ArduinoTool(BaseTool):
    @property
    def name(self):
        return "/arduino"

    @property
    def description(self):
        return "Generate Arduino code."

    @property
    def cost(self):
        return 1

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"Write Arduino code to: {user_input}"
        output = await llm_client.generate(
            prompt, provider="nvidia", model=settings.NVIDIA_CODING_MODEL
        )
        return {"status": "success", "output": output, "tokens_deducted": self.cost}


# --- Local Dev Utils ---


class TimestampTool(BaseTool):
    @property
    def name(self):
        return "/timestamp"

    @property
    def description(self):
        return "Get current unix timestamp."

    @property
    def cost(self):
        return 0

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        return {
            "status": "success",
            "output": str(int(time.time())),
            "tokens_deducted": 0,
        }


class HashTool(BaseTool):
    @property
    def name(self):
        return "/hash"

    @property
    def description(self):
        return "Calculate SHA256 hash."

    @property
    def cost(self):
        return 0

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        h = hashlib.sha256(user_input.encode()).hexdigest()
        return {"status": "success", "output": f"SHA256: `{h}`", "tokens_deducted": 0}


class LoremTool(BaseTool):
    @property
    def name(self):
        return "/lorem"

    @property
    def description(self):
        return "Generate Lorem Ipsum."

    @property
    def cost(self):
        return 0

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        paragraphs = [
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
            "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
            "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo.",
        ]
        count = 1
        if user_input.strip().isdigit():
            count = min(int(user_input.strip()), 5)
        output = "\n\n".join(paragraphs[:count])
        return {"status": "success", "output": output, "tokens_deducted": 0}


# Placeholder for others
class JsonTool(BaseTool):
    @property
    def name(self):
        return "/json_format"

    @property
    def description(self):
        return "Format JSON string."

    @property
    def cost(self):
        return 0

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        import json

        try:
            parsed = json.loads(user_input)
            formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
            return {
                "status": "success",
                "output": f"```json\n{formatted}\n```",
                "tokens_deducted": 0,
            }
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "output": f"Invalid JSON: {str(e)}",
                "tokens_deducted": 0,
            }


class Base64Tool(BaseTool):
    @property
    def name(self):
        return "/base64"

    @property
    def description(self):
        return "Encode text to base64."

    @property
    def cost(self):
        return 0

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        import base64

        return {
            "status": "success",
            "output": base64.b64encode(user_input.encode()).decode(),
            "tokens_deducted": 0,
        }
