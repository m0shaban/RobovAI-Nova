from typing import Dict, Any
from .base import BaseTool
import httpx
from backend.core.llm import llm_client

# --- AI Powered Tools ---

class RoastTool(BaseTool):
    @property
    def name(self): return "/roast"
    @property
    def description(self): return "Roast a profile or text."
    @property
    def cost(self): return 1
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"Give a savage, funny roast for: {user_input}"
        output = await llm_client.generate(prompt, provider="auto", system_prompt="You are a clear-cut roast master.")
        return {"status": "success", "output": output, "tokens_deducted": self.cost}

class RizzTool(BaseTool):
    @property
    def name(self): return "/rizz"
    @property
    def description(self): return "Generate a smooth pickup line or reply."
    @property
    def cost(self): return 1
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"Generate a smooth, witty 'rizz' reply to: {user_input}"
        output = await llm_client.generate(prompt, provider="auto")
        return {"status": "success", "output": output, "tokens_deducted": self.cost}

class DreamTool(BaseTool):
    @property
    def name(self): return "/dream"
    @property
    def description(self): return "Interpret a dream."
    @property
    def cost(self): return 1
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"Interpret this dream psychologically: {user_input}"
        output = await llm_client.generate(prompt, provider="auto")
        return {"status": "success", "output": output, "tokens_deducted": self.cost}

class HoroscopeTool(BaseTool):
    @property
    def name(self): return "/horoscope"
    @property
    def description(self): return "Daily horoscope for a sign."
    @property
    def cost(self): return 1
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"Give a funny and accurate daily horoscope for: {user_input}"
        output = await llm_client.generate(prompt, provider="auto")
        return {"status": "success", "output": output, "tokens_deducted": self.cost}

class FightTool(BaseTool):
    @property
    def name(self): return "/fight"
    @property
    def description(self): return "Simulate a funny fight between two things."
    @property
    def cost(self): return 1
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"Simulate a short funny fight scenario between: {user_input}"
        output = await llm_client.generate(prompt, provider="auto")
        return {"status": "success", "output": output, "tokens_deducted": self.cost}

# --- API Powered Tools ---

class JokeTool(BaseTool):
    @property
    def name(self): return "/joke"
    @property
    def description(self): return "Get a random joke."
    @property
    def cost(self): return 0
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://official-joke-api.appspot.com/random_joke")
            data = resp.json()
            return {"status": "success", "output": f"{data['setup']}\n\n{data['punchline']}", "tokens_deducted": self.cost}

class CatTool(BaseTool):
    @property
    def name(self): return "/cat"
    @property
    def description(self): return "Get a random cat image."
    @property
    def cost(self): return 0
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://api.thecatapi.com/v1/images/search")
            data = resp.json()
            return {"status": "success", "output": f"![Cat]({data[0]['url']})", "tokens_deducted": self.cost}

class DogTool(BaseTool):
    @property
    def name(self): return "/dog"
    @property
    def description(self): return "Get a random dog image."
    @property
    def cost(self): return 0
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://dog.ceo/api/breeds/image/random")
            data = resp.json()
            return {"status": "success", "output": f"![Dog]({data['message']})", "tokens_deducted": self.cost}

class BoredTool(BaseTool):
    @property
    def name(self): return "/bored"
    @property
    def description(self): return "Get an activity idea."
    @property
    def cost(self): return 0
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://bored-api.appbrewery.com/random")
            if resp.status_code == 200:
                data = resp.json()
                return {"status": "success", "output": f"Activity: {data['activity']}\nType: {data['type']}", "tokens_deducted": self.cost}
            else:
                 return {"status": "error", "output": "Could not fetch activity.", "tokens_deducted": 0}

class TriviaTool(BaseTool):
    @property
    def name(self): return "/trivia"
    @property
    def description(self): return "Get a trivia question."
    @property
    def cost(self): return 0
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
         async with httpx.AsyncClient() as client:
            resp = await client.get("https://opentdb.com/api.php?amount=1&type=boolean")
            data = resp.json()
            q = data['results'][0]
            return {"status": "success", "output": f"Category: {q['category']}\nQ: {q['question']}\nA: {q['correct_answer']}", "tokens_deducted": self.cost}
