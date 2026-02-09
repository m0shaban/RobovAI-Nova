"""
Quote Generator Tool - مولد اقتباسات (Fixed)
"""

import httpx
from typing import Dict, Any
from .base import BaseTool
import random


class QuoteTool(BaseTool):
    """
    أداة الاقتباسات الملهمة
    """

    # Fallback quotes in case API fails
    FALLBACK_QUOTES = [
        {
            "content": "النجاح ليس نهائياً، والفشل ليس قاتلاً: إنها الشجاعة للاستمرار هي ما يهم.",
            "author": "وينستون تشرشل",
        },
        {
            "content": "الطريقة الوحيدة للقيام بعمل عظيم هي أن تحب ما تفعله.",
            "author": "ستيف جوبز",
        },
        {
            "content": "ابدأ من حيث أنت، استخدم ما لديك، وافعل ما تستطيع.",
            "author": "آرثر آش",
        },
        {
            "content": "الإيمان هو الطير الذي يشعر بالنور عندما يكون الفجر لا يزال مظلماً.",
            "author": "طاغور",
        },
        {"content": "لا تخف من الفشل، بل خف من عدم المحاولة.", "author": "روي بينيت"},
        {
            "content": "المستقبل ينتمي لأولئك الذين يؤمنون بجمال أحلامهم.",
            "author": "إليانور روزفلت",
        },
        {"content": "العلم نور والجهل ظلام.", "author": "حكمة عربية"},
        {"content": "من جد وجد ومن زرع حصد.", "author": "مثل عربي"},
        {"content": "اطلبوا العلم ولو في الصين.", "author": "حديث شريف"},
        {"content": "خير الناس أنفعهم للناس.", "author": "حديث شريف"},
    ]

    @property
    def name(self) -> str:
        return "/quote"

    @property
    def description(self) -> str:
        return "💬 اقتباس ملهم - اقتباسات تحفيزية"

    @property
    def cost(self) -> int:
        return 5

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        الحصول على اقتباس ملهم عشوائي
        """

        try:
            # Try ZenQuotes API (free, no SSL issues)
            url = "https://zenquotes.io/api/random"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

            if data and len(data) > 0:
                quote = data[0].get("q", "")
                author = data[0].get("a", "Unknown")

                output = f"""💬 **اقتباس ملهم**

"{quote}"

**— {author}**

---
✨ كن ملهماً اليوم!"""

                return {
                    "status": "success",
                    "output": output,
                    "tokens_deducted": self.cost,
                }
        except:
            pass

        # Fallback to local quotes
        quote_data = random.choice(self.FALLBACK_QUOTES)

        output = f"""💬 **اقتباس ملهم**

"{quote_data['content']}"

**— {quote_data['author']}**

---
✨ كن ملهماً اليوم!"""

        return {"status": "success", "output": output, "tokens_deducted": self.cost}
