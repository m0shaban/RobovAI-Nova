"""
🔍 Deep Research Tool - Multi-source research aggregation
"""

from backend.tools.base import BaseTool
from typing import Dict, Any, List
import httpx
import asyncio
from bs4 import BeautifulSoup


class DeepResearchTool(BaseTool):
    """
    بحث عميق متعدد المصادر مع تجميع وتحليل النتائج
    """

    @property
    def name(self) -> str:
        return "/deep_research"

    @property
    def description(self) -> str:
        return "بحث عميق متعدد المصادر (Wikipedia, DuckDuckGo, Web) مع تجميع النتائج وتحليلها"

    @property
    def cost(self) -> int:
        return 3

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        تنفيذ بحث عميق من مصادر متعددة
        """
        try:
            query = user_input.strip()

            if not query:
                return {
                    "status": "error",
                    "output": "❌ يرجى تحديد موضوع البحث",
                    "tokens_deducted": 0,
                }

            # تنفيذ البحث من مصادر متعددة بالتوازي
            results = await asyncio.gather(
                self._search_wikipedia(query),
                self._search_duckduckgo(query),
                return_exceptions=True,
            )

            # تجميع النتائج
            wikipedia_result = (
                results[0] if not isinstance(results[0], Exception) else None
            )
            duckduckgo_result = (
                results[1] if not isinstance(results[1], Exception) else None
            )

            # بناء التقرير
            report = self._build_report(query, wikipedia_result, duckduckgo_result)

            return {
                "status": "success",
                "output": report,
                "tokens_deducted": self.cost,
                "sources": {
                    "wikipedia": bool(wikipedia_result),
                    "duckduckgo": bool(duckduckgo_result),
                },
            }

        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ في البحث: {str(e)}",
                "tokens_deducted": 0,
            }

    async def _search_wikipedia(self, query: str) -> Dict[str, Any]:
        """بحث في ويكيبيديا"""
        try:
            headers = {
                "User-Agent": "RobovAI-Nova/1.0 (https://robovai.com; contact@robovai.com)"
            }
            async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
                # بحث بالعربي أولاً
                response = await client.get(
                    "https://ar.wikipedia.org/w/api.php",
                    params={
                        "action": "query",
                        "format": "json",
                        "list": "search",
                        "srsearch": query,
                        "srlimit": 3,
                    },
                )

                data = response.json()
                results = data.get("query", {}).get("search", [])

                if not results:
                    # جرب بالإنجليزي
                    response = await client.get(
                        "https://en.wikipedia.org/w/api.php",
                        params={
                            "action": "query",
                            "format": "json",
                            "list": "search",
                            "srsearch": query,
                            "srlimit": 3,
                        },
                    )
                    data = response.json()
                    results = data.get("query", {}).get("search", [])

                return {
                    "source": "Wikipedia",
                    "results": [
                        {
                            "title": r.get("title"),
                            "snippet": BeautifulSoup(
                                r.get("snippet", ""), "html.parser"
                            ).get_text(),
                        }
                        for r in results[:3]
                    ],
                }
        except Exception as e:
            return {"source": "Wikipedia", "error": str(e)}

    async def _search_duckduckgo(self, query: str) -> Dict[str, Any]:
        """بحث في DuckDuckGo"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.duckduckgo.com/",
                    params={"q": query, "format": "json", "no_html": 1},
                )

                data = response.json()

                return {
                    "source": "DuckDuckGo",
                    "abstract": data.get("Abstract", ""),
                    "related": [
                        {"title": t.get("Text"), "url": t.get("FirstURL")}
                        for t in data.get("RelatedTopics", [])[:5]
                        if isinstance(t, dict) and "Text" in t
                    ],
                }
        except Exception as e:
            return {"source": "DuckDuckGo", "error": str(e)}

    def _build_report(
        self, query: str, wikipedia: Dict[str, Any], duckduckgo: Dict[str, Any]
    ) -> str:
        """بناء تقرير البحث"""

        report = f"📊 **نتائج البحث العميق عن: {query}**\n\n"

        # نتائج Wikipedia
        if wikipedia and "results" in wikipedia:
            report += "### 📚 من ويكيبيديا:\n\n"
            for r in wikipedia["results"]:
                report += f"**{r['title']}**\n"
                report += f"{r['snippet']}\n\n"

        # نتائج DuckDuckGo
        if duckduckgo and "abstract" in duckduckgo and duckduckgo["abstract"]:
            report += "### 🔍 من DuckDuckGo:\n\n"
            report += f"{duckduckgo['abstract']}\n\n"

        if duckduckgo and "related" in duckduckgo and duckduckgo["related"]:
            report += "**مواضيع ذات صلة:**\n"
            for r in duckduckgo["related"][:3]:
                report += f"- {r['title']}\n"

        if not wikipedia and not duckduckgo:
            report += "⚠️ لم يتم العثور على نتائج من المصادر المتاحة."

        return report
