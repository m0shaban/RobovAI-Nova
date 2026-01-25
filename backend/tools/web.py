from typing import Dict, Any
from .base import BaseTool
import logging
import json

logger = logging.getLogger("robovai.tools.web")

# --- 1. DuckDuckGo Search ---
try:
    from duckduckgo_search import DDGS
    DDG_AVAILABLE = True
except ImportError:
    DDG_AVAILABLE = False

class SearchTool(BaseTool):
    @property
    def name(self) -> str:
        return "/search"

    @property
    def description(self) -> str:
        return "Search the web for real-time information."

    @property
    def cost(self) -> int:
        return 0

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        if not DDG_AVAILABLE:
            return {"status": "error", "output": "⚠️ Missing dependency: duckduckgo-search"}
        
        if not user_input.strip():
             return {"status": "error", "output": "❌ Please provide a search query."}

        try:
            results = DDGS().text(user_input, max_results=5)
            if not results:
                return {"status": "success", "output": "⚠️ No results found."}
            
            # Format results
            msg = f"🔍 **Search Results for:** `{user_input}`\n\n"
            for r in results:
                msg += f"🔹 [{r['title']}]({r['href']})\n{r['body']}\n\n"
            
            return {"status": "success", "output": msg.strip()}
        except Exception as e:
            logger.error(f"Search Error: {e}")
            return {"status": "error", "output": f"❌ Search failed: {e}"}


# --- 2. YFinance Stock ---
try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False

class FinanceTool(BaseTool):
    @property
    def name(self) -> str:
        return "/stock"

    @property
    def description(self) -> str:
        return "Get stock price and info (e.g. /stock AAPL)"

    @property
    def cost(self) -> int:
        return 0

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        if not YF_AVAILABLE:
             return {"status": "error", "output": "⚠️ Missing dependency: yfinance"}
        
        ticker_symbol = user_input.strip().upper()
        if not ticker_symbol:
            return {"status": "error", "output": "❌ Please provide a ticker symbol (e.g. AAPL, TSLA)."}

        try:
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info
            
            # Basic info might vary, handle gracefully
            price = info.get('currentPrice') or info.get('regularMarketPrice')
            currency = info.get('currency', 'USD')
            name = info.get('longName', ticker_symbol)
            summary = info.get('longBusinessSummary', 'No summary.')[:200] + "..."
            
            msg = f"""📈 **Stock Report: {name} ({ticker_symbol})**
            
💰 **Price**: {price} {currency}
🏢 **Sector**: {info.get('sector', 'N/A')}
⚠️ **Risk**: {info.get('auditRisk', 'N/A')}

📝 **Summary**:
{summary}
"""
            return {"status": "success", "output": msg}
        except Exception as e:
            return {"status": "error", "output": f"❌ Finance Error: {e}"}


# --- 3. Media Downloader (YT-DLP) ---
# Note: yt-dlp requires ffmpeg commonly for best results.
# On Render free tier, we might not have ffmpeg installed in base image.
# We will use basic extraction that works without binary if possible, or warn user.

try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False

class MediaTool(BaseTool):
    @property
    def name(self) -> str:
        return "/download"

    @property
    def description(self) -> str:
        return "Download video info/link from URL"

    @property
    def cost(self) -> int:
        return 0

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        if not YTDLP_AVAILABLE:
            return {"status": "error", "output": "⚠️ Missing dependency: yt-dlp"}

        url = user_input.strip()
        if not url.startswith("http"):
             return {"status": "error", "output": "❌ Invalid URL."}
             
        ydl_opts = {
            'format': 'best',
            'noplaylist': True,
            'quiet': True,
            'simulate': True, # crucial on server to not fill disk
            'forceurl': True, # just get the direct link
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'Video')
                video_url = info.get('url')
                duration = info.get('duration_string')
                
                # Check for direct download link (often expires fast)
                msg = f"""🎬 **Video Found:** {title}
⏱️ **Duration**: {duration}

🔗 **Direct Link (Click to Watch/Down):**
{video_url}

*(Link expires internally, open immediately)*
"""
                return {"status": "success", "output": msg}
        except Exception as e:
            return {"status": "error", "output": f"❌ Download Error: {e}"}
