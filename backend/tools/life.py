from typing import Dict, Any
from .base import BaseTool
import httpx
from backend.core.llm import llm_client

# --- Info APIs ---

class WeatherTool(BaseTool):
    @property
    def name(self): return "/weather"
    @property
    def description(self): return "Get weather info."
    @property
    def cost(self): return 0
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        # Using OpenMeteo for free weather
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://api.open-meteo.com/v1/forecast?latitude=30.04&longitude=31.23&current_weather=true") # Default Cairo
            data = resp.json()
            w = data['current_weather']
            return {"status": "success", "output": f"Cairo Temp: {w['temperature']}C\nWind: {w['windspeed']} km/h", "tokens_deducted": self.cost}

class WikiTool(BaseTool):
    @property
    def name(self): return "/wiki"
    @property
    def description(self): return "Search Wikipedia."
    @property
    def cost(self): return 0
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        return {"status": "success", "output": f"Here is a summary from Wikipedia for '{user_input}' (Mocked)", "tokens_deducted": 0}

class DefinitionTool(BaseTool):
    @property
    def name(self): return "/definition"
    @property
    def description(self): return "Define a word."
    @property
    def cost(self): return 0
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{user_input}")
            if resp.status_code == 200:
                data = resp.json()[0]
                meaning = data['meanings'][0]['definitions'][0]['definition']
                return {"status": "success", "output": f"Definition: {meaning}", "tokens_deducted": self.cost}
            return {"status": "error", "output": "Word not found", "tokens_deducted": 0}

class NumberFactTool(BaseTool):
    @property
    def name(self): return "/number_fact"
    @property
    def description(self): return "Fun fact about a number."
    @property
    def cost(self): return 0
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        num = user_input if user_input.isdigit() else "random"
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"http://numbersapi.com/{num}/math")
            return {"status": "success", "output": resp.text, "tokens_deducted": 0}

class HolidayTool(BaseTool):
    @property
    def name(self): return "/holiday"
    @property
    def description(self): return "Is today a holiday?"
    @property
    def cost(self): return 0
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        return {"status": "success", "output": "Today is not a public holiday.", "tokens_deducted": 0}

# --- Lifestyle AI ---

class TravelPlanTool(BaseTool):
    @property
    def name(self): return "/travel_plan"
    @property
    def description(self): return "Plan a trip."
    @property
    def cost(self): return 1
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"Create a 3-day travel itinerary for: {user_input}"
        output = await llm_client.generate(prompt, provider="groq")
        return {"status": "success", "output": output, "tokens_deducted": self.cost}

class MealPlanTool(BaseTool):
    @property
    def name(self): return "/meal_plan"
    @property
    def description(self): return "Weekly meal prep."
    @property
    def cost(self): return 1
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"Create a healthy meal plan for: {user_input}"
        output = await llm_client.generate(prompt, provider="groq")
        return {"status": "success", "output": output, "tokens_deducted": self.cost}

class WorkoutTool(BaseTool):
    @property
    def name(self): return "/workout"
    @property
    def description(self): return "Workout routine."
    @property
    def cost(self): return 1
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"Create a gym workout for: {user_input}"
        output = await llm_client.generate(prompt, provider="groq")
        return {"status": "success", "output": output, "tokens_deducted": self.cost}

class GiftTool(BaseTool):
    @property
    def name(self): return "/gift"
    @property
    def description(self): return "Gift ideas."
    @property
    def cost(self): return 1
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"Gift ideas for: {user_input}"
        output = await llm_client.generate(prompt, provider="groq")
        return {"status": "success", "output": output, "tokens_deducted": self.cost}

class MovieRecTool(BaseTool):
    @property
    def name(self): return "/movie_rec"
    @property
    def description(self): return "Movie recommendation."
    @property
    def cost(self): return 1
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"Recommend 3 movies similar to: {user_input}"
        output = await llm_client.generate(prompt, provider="groq")
        return {"status": "success", "output": output, "tokens_deducted": self.cost}
