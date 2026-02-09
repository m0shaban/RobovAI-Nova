"""
Random Facts Tool - حقائق عشوائية (Fixed)
"""

import httpx
from typing import Dict, Any
from .base import BaseTool


class RandomFactTool(BaseTool):
    """
    أداة الحقائق العشوائية
    """

    @property
    def name(self) -> str:
        return "/fact"

    @property
    def description(self) -> str:
        return "💡 حقيقة عشوائية - حقائق مثيرة ومفيدة"

    @property
    def cost(self) -> int:
        return 5

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        الحصول على حقيقة عشوائية
        """

        try:
            # Updated URL (API v2)
            url = "https://uselessfacts.jsph.pl/api/v2/facts/random?language=en"

            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

            fact = data.get("text", "No fact available")
            source = data.get("source", "Unknown")

            output = f"""💡 **حقيقة عشوائية**

{fact}

📚 المصدر: {source}

---
🌟 هل كنت تعرف؟"""

            return {"status": "success", "output": output, "tokens_deducted": self.cost}

        except Exception as e:
            # Fallback to a different free API
            try:
                async with httpx.AsyncClient(
                    timeout=10.0, follow_redirects=True
                ) as client:
                    response = await client.get(
                        "https://fungenerators.com/random/facts/"
                    )
                    # Simple fallback with a basic fact
                    pass
            except:
                pass

            # Final fallback: local facts
            import random

            local_facts = [
                "Honey never spoils. Archaeologists have found 3000-year-old honey in Egyptian tombs that was still edible.",
                "Octopuses have three hearts, nine brains, and blue blood.",
                "A group of flamingos is called a 'flamboyance'.",
                "Bananas are berries, but strawberries aren't.",
                "The shortest war in history lasted 38 minutes (Britain vs Zanzibar, 1896).",
                "A day on Venus is longer than a year on Venus.",
                "The inventor of the Pringles can is buried in one.",
                "Cows have best friends and get stressed when separated.",
            ]
            fact = random.choice(local_facts)
            return {
                "status": "success",
                "output": f"💡 **حقيقة عشوائية**\n\n{fact}\n\n---\n🌟 هل كنت تعرف؟",
                "tokens_deducted": self.cost,
            }
