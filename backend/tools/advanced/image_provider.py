"""
🖼️ Smart Image Provider — Multi-source image fetching
Sources:  Unsplash API  |  Pexels API  |  Pollinations AI  |  Placeholder
"""
import httpx
import os
import logging
from typing import List, Dict
from urllib.parse import quote

logger = logging.getLogger("robovai.images")


class ImageProvider:
    """Fetches presentation-quality images with automatic fallback."""

    def __init__(self):
        self.unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY", "")
        self.pexels_key = os.getenv("PEXELS_API_KEY", "")

    # ─── public API ─────────────────────────────────────────────
    async def get_images(
        self,
        query: str,
        count: int = 6,
        source: str = "auto",
    ) -> List[Dict[str, str]]:
        """
        Return up to *count* images.
        Each item: {"url": "...", "credit": "...", "source": "..."}
        *source*: auto | unsplash | pexels | ai | none
        """
        if source == "none":
            return []

        dispatch = {
            "unsplash": self._unsplash,
            "pexels": self._pexels,
            "ai": self._pollinations,
        }

        if source != "auto":
            fn = dispatch.get(source)
            if fn:
                imgs = await fn(query, count)
                if imgs:
                    return imgs
            return self._placeholder(query, count)

        # auto — waterfall: Unsplash → Pexels → Pollinations → placeholder
        for name, fn in dispatch.items():
            try:
                imgs = await fn(query, count)
                if imgs and len(imgs) >= min(count, 2):
                    logger.info(f"📸 Got {len(imgs)} images from {name}")
                    return imgs[:count]
            except Exception as e:
                logger.warning(f"Image source {name} failed: {e}")
        return self._placeholder(query, count)

    # ─── Unsplash ───────────────────────────────────────────────
    async def _unsplash(self, query: str, count: int) -> List[Dict[str, str]]:
        if not self.unsplash_key:
            return []
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                "https://api.unsplash.com/search/photos",
                params={"query": query, "per_page": count, "orientation": "landscape"},
                headers={"Authorization": f"Client-ID {self.unsplash_key}"},
            )
            if r.status_code != 200:
                return []
            return [
                {
                    "url": p["urls"]["regular"],
                    "credit": f"Photo by {p['user']['name']} on Unsplash",
                    "source": "unsplash",
                }
                for p in r.json().get("results", [])
            ]

    # ─── Pexels ─────────────────────────────────────────────────
    async def _pexels(self, query: str, count: int) -> List[Dict[str, str]]:
        if not self.pexels_key:
            return []
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                "https://api.pexels.com/v1/search",
                params={"query": query, "per_page": count, "orientation": "landscape"},
                headers={"Authorization": self.pexels_key},
            )
            if r.status_code != 200:
                return []
            return [
                {
                    "url": p["src"]["large"],
                    "credit": f"Photo by {p['photographer']} on Pexels",
                    "source": "pexels",
                }
                for p in r.json().get("photos", [])
            ]

    # ─── Pollinations AI ────────────────────────────────────────
    async def _pollinations(self, query: str, count: int) -> List[Dict[str, str]]:
        base = "https://image.pollinations.ai/prompt"
        prompt_text = f"{query}, professional photo, HD, 16:9, high quality"
        encoded = quote(prompt_text)
        return [
            {
                "url": f"{base}/{encoded}?width=960&height=540&seed={i}&nologo=true",
                "credit": "AI Generated · Pollinations",
                "source": "ai",
            }
            for i in range(count)
        ]

    # ─── Placeholder ────────────────────────────────────────────
    @staticmethod
    def _placeholder(query: str, count: int) -> List[Dict[str, str]]:
        q = quote(query)
        return [
            {
                "url": f"https://placehold.co/960x540/667eea/white?text={q}",
                "credit": "",
                "source": "placeholder",
            }
            for _ in range(count)
        ]


image_provider = ImageProvider()
