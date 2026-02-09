from typing import Dict, Any
from .base import BaseTool
import httpx
from backend.core.llm import llm_client

# --- Info APIs ---


class WeatherTool(BaseTool):
    @property
    def name(self):
        return "/weather"

    @property
    def description(self):
        return "Get weather info."

    @property
    def cost(self):
        return 0

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        # Using OpenMeteo for free weather
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.open-meteo.com/v1/forecast?latitude=30.04&longitude=31.23&current_weather=true"
            )  # Default Cairo
            data = resp.json()
            w = data["current_weather"]
            return {
                "status": "success",
                "output": f"Cairo Temp: {w['temperature']}C\nWind: {w['windspeed']} km/h",
                "tokens_deducted": self.cost,
            }


class WikiTool(BaseTool):
    @property
    def name(self):
        return "/wiki"

    @property
    def description(self):
        return "Search Wikipedia."

    @property
    def cost(self):
        return 0

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        query = user_input.strip() or "Wikipedia"
        try:
            headers = {
                "User-Agent": "RobovAI-Nova/1.0 (https://robovai.com; contact@robovai.com)"
            }
            async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
                resp = await client.get(
                    "https://ar.wikipedia.org/w/api.php",
                    params={
                        "action": "query",
                        "format": "json",
                        "list": "search",
                        "srsearch": query,
                        "srlimit": 1,
                    },
                )
                data = resp.json()
                results = data.get("query", {}).get("search", [])
                lang = "ar"

                if not results:
                    # Fallback to English
                    resp = await client.get(
                        "https://en.wikipedia.org/w/api.php",
                        params={
                            "action": "query",
                            "format": "json",
                            "list": "search",
                            "srsearch": query,
                            "srlimit": 1,
                        },
                    )
                    data = resp.json()
                    results = data.get("query", {}).get("search", [])
                    lang = "en"

                if results:
                    title = results[0]["title"]
                    # Get extract
                    resp2 = await client.get(
                        f"https://{lang}.wikipedia.org/w/api.php",
                        params={
                            "action": "query",
                            "format": "json",
                            "prop": "extracts",
                            "exintro": True,
                            "explaintext": True,
                            "titles": title,
                        },
                    )
                    pages = resp2.json().get("query", {}).get("pages", {})
                    extract = list(pages.values())[0].get(
                        "extract", "No extract available."
                    )
                    url = f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}"
                    return {
                        "status": "success",
                        "output": f"📚 **{title}**\n\n{extract[:1000]}\n\n🔗 [Read more]({url})",
                        "tokens_deducted": 0,
                    }

                return {
                    "status": "error",
                    "output": f"No Wikipedia results for '{query}'",
                    "tokens_deducted": 0,
                }
        except Exception as e:
            return {
                "status": "error",
                "output": f"Wikipedia error: {str(e)}",
                "tokens_deducted": 0,
            }


class DefinitionTool(BaseTool):
    @property
    def name(self):
        return "/definition"

    @property
    def description(self):
        return "Define a word."

    @property
    def cost(self):
        return 0

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.dictionaryapi.dev/api/v2/entries/en/{user_input}"
            )
            if resp.status_code == 200:
                data = resp.json()[0]
                meaning = data["meanings"][0]["definitions"][0]["definition"]
                return {
                    "status": "success",
                    "output": f"Definition: {meaning}",
                    "tokens_deducted": self.cost,
                }
            return {"status": "error", "output": "Word not found", "tokens_deducted": 0}


class NumberFactTool(BaseTool):
    @property
    def name(self):
        return "/number_fact"

    @property
    def description(self):
        return "Fun fact about a number."

    @property
    def cost(self):
        return 0

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        num = user_input if user_input.isdigit() else "random"
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"http://numbersapi.com/{num}/math")
            return {"status": "success", "output": resp.text, "tokens_deducted": 0}


class HolidayTool(BaseTool):
    @property
    def name(self):
        return "/holiday"

    @property
    def description(self):
        return "Is today a holiday?"

    @property
    def cost(self):
        return 0

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        from datetime import datetime

        try:
            now = datetime.now()
            year, month, day = now.year, now.month, now.day
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"https://date.nager.at/api/v3/PublicHolidays/{year}/EG"
                )
                if resp.status_code == 200:
                    holidays = resp.json()
                    today_str = f"{year}-{month:02d}-{day:02d}"
                    today_holidays = [h for h in holidays if h.get("date") == today_str]
                    if today_holidays:
                        names = ", ".join(
                            h.get("localName", h.get("name", ""))
                            for h in today_holidays
                        )
                        return {
                            "status": "success",
                            "output": f"🎉 نعم! النهاردة عيد: {names}",
                            "tokens_deducted": 0,
                        }
                    else:
                        # Find next holiday
                        upcoming = [
                            h for h in holidays if h.get("date", "") > today_str
                        ]
                        if upcoming:
                            nxt = upcoming[0]
                            return {
                                "status": "success",
                                "output": f"📅 النهاردة مش عيد.\n\nأقرب أجازة: {nxt.get('localName', nxt.get('name'))} بتاريخ {nxt['date']}",
                                "tokens_deducted": 0,
                            }
                        return {
                            "status": "success",
                            "output": "📅 النهاردة مش عيد رسمي.",
                            "tokens_deducted": 0,
                        }
            return {
                "status": "success",
                "output": "📅 النهاردة مش عيد رسمي.",
                "tokens_deducted": 0,
            }
        except Exception as e:
            return {
                "status": "error",
                "output": f"Holiday API error: {str(e)}",
                "tokens_deducted": 0,
            }


# --- Lifestyle AI ---


class TravelPlanTool(BaseTool):
    @property
    def name(self):
        return "/travel_plan"

    @property
    def description(self):
        return "Plan a trip."

    @property
    def cost(self):
        return 1

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"Create a 3-day travel itinerary for: {user_input}"
        output = await llm_client.generate(prompt, provider="auto")
        return {"status": "success", "output": output, "tokens_deducted": self.cost}


class MealPlanTool(BaseTool):
    @property
    def name(self):
        return "/meal_plan"

    @property
    def description(self):
        return "Weekly meal prep."

    @property
    def cost(self):
        return 1

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"Create a healthy meal plan for: {user_input}"
        output = await llm_client.generate(prompt, provider="auto")
        return {"status": "success", "output": output, "tokens_deducted": self.cost}


class WorkoutTool(BaseTool):
    @property
    def name(self):
        return "/workout"

    @property
    def description(self):
        return "Workout routine."

    @property
    def cost(self):
        return 1

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"Create a gym workout for: {user_input}"
        output = await llm_client.generate(prompt, provider="auto")
        return {"status": "success", "output": output, "tokens_deducted": self.cost}


class GiftTool(BaseTool):
    @property
    def name(self):
        return "/gift"

    @property
    def description(self):
        return "Gift ideas."

    @property
    def cost(self):
        return 1

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"Gift ideas for: {user_input}"
        output = await llm_client.generate(prompt, provider="auto")
        return {"status": "success", "output": output, "tokens_deducted": self.cost}


class MovieRecTool(BaseTool):
    @property
    def name(self):
        return "/movie_rec"

    @property
    def description(self):
        return "Movie recommendation."

    @property
    def cost(self):
        return 1

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        prompt = f"Recommend 3 movies similar to: {user_input}"
        output = await llm_client.generate(prompt, provider="auto")
        return {"status": "success", "output": output, "tokens_deducted": self.cost}
