"""
🕸️ Web Scraper Tool - Advanced Content Extraction
"""

from backend.tools.base import BaseTool
from typing import Dict, Any, Type, Optional
from pydantic import BaseModel, Field
import httpx
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger("robovai.tools.scraper")


class ScrapeSchema(BaseModel):
    url: str = Field(..., description="The URL to scrape content from")
    include_links: bool = Field(
        False, description="Whether to extract links from the page"
    )
    max_length: int = Field(5000, description="Maximum length of content to return")


class WebScraperTool(BaseTool):
    """
    Advanced Web Scraper to read content from websites.
    Capable of cleaning HTML and extracting meaningful text.
    """

    @property
    def name(self) -> str:
        return "/scrape_url"

    @property
    def description(self) -> str:
        return "Extract clean text content from any website URL."

    @property
    def cost(self) -> int:
        return 3

    @property
    def args_schema(self) -> Type[BaseModel]:
        return ScrapeSchema

    async def execute_kwargs(
        self,
        user_id: str,
        url: str,
        include_links: bool = False,
        max_length: int = 5000,
    ) -> Dict[str, Any]:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Remove scripts and styles
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.extract()

            # Get text
            text = soup.get_text()

            # Break into lines and remove leading and trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Drop blank lines
            text = "\n".join(chunk for chunk in chunks if chunk)

            # Truncate
            truncated = len(text) > max_length
            final_text = text[:max_length] + ("... (truncated)" if truncated else "")

            result = {
                "url": url,
                "title": soup.title.string if soup.title else "No Title",
                "content": final_text,
                "length": len(final_text),
            }

            if include_links:
                links = []
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if href.startswith("http"):
                        links.append({"text": a.get_text(strip=True), "url": href})
                result["links"] = links[:20]  # Limit links

            return {
                "status": "success",
                "output": final_text,  # Return main content as primary output string for LLM
                "data": result,  # Structured data used if needed programmatically
            }

        except Exception as e:
            return {"status": "error", "output": f"Failed to scrape {url}: {str(e)}"}

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """Legacy string execution"""
        # Try to parse url from input
        url = user_input.strip()
        if not url.startswith("http"):
            # Heuristic: try to find http in string
            import re

            match = re.search(r"https?://[^\s]+", url)
            if match:
                url = match.group(0)
            else:
                return {"status": "error", "output": "Invalid URL provided."}

        return await self.execute_kwargs(user_id, url)
