from typing import Dict, Any
from .base import BaseTool
from backend.core.llm import llm_client
from backend.core.config import settings

# --- Safety & Business Intelligence Tools ---

class CheckContentTool(BaseTool):
    @property
    def name(self): return "/check_content"
    @property
    def description(self): return "فحص أمان المحتوى قبل النشر"
    @property
    def cost(self): return 2
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        # In production: Use nemotron-content-safety-reasoning-4b + nemoguard-jailbreak
        prompt = f"Check if this content is safe to publish (toxicity, hate, violence, etc.): {user_input}"
        output = await llm_client.generate(
            prompt,
            provider="nvidia",
            model="nvidia/nemotron-content-safety-reasoning-4b",
            system_prompt="You are a content safety moderator. Rate content safety 1-10 and explain risks."
        )
        return {"status": "success", "output": f"🛡️ Safety Check:\n{output}", "tokens_deducted": self.cost}


class LegalSummaryTool(BaseTool):
    @property
    def name(self): return "/legal_summary"
    @property
    def description(self): return "تلخيص العقود القانونية بالعربي"
    @property
    def cost(self): return 10
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        # user_input = contract PDF URL or text
        prompt = f"Summarize this legal contract in simple Egyptian Arabic, highlighting key obligations, risks, and terms:\n\n{user_input}"
        output = await llm_client.generate(
            prompt,
            provider="nvidia",
            model=settings.NVIDIA_GENERAL_MODEL,
            system_prompt="You are a legal advisor. Simplify contracts for non-lawyers."
        )
        return {"status": "success", "output": f"⚖️ Contract Summary:\n{output}", "tokens_deducted": self.cost}


class OutfitRateTool(BaseTool):
    @property
    def name(self): return "/outfit_rate"
    @property
    def description(self): return "تقييم الملابس من صورة 👔"
    @property
    def cost(self): return 2
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        # user_input = outfit image URL
        prompt = f"Rate this outfit 1-10 and give fashion advice: {user_input}"
        output = await llm_client.generate(
            prompt,
            provider="nvidia",
            model="nvidia/cosmos-nemotron-34b",
            system_prompt="You are a fashion expert. Be encouraging but honest."
        )
        return {"status": "success", "output": f"👔 Fashion Rating:\n{output}", "tokens_deducted": self.cost}


class DishRecipeTool(BaseTool):
    @property
    def name(self): return "/dish_recipe"
    @property
    def description(self): return "استخراج الوصفة من صورة طبق 🍲"
    @property
    def cost(self): return 3
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        # user_input = dish image URL
        prompt = f"Identify this dish and provide the full recipe: {user_input}"
        output = await llm_client.generate(
            prompt,
            provider="nvidia",
            model="nvidia/cosmos-nemotron-34b"
        )
        return {"status": "success", "output": f"🍲 Recipe:\n{output}", "tokens_deducted": self.cost}


class CompareOffersTool(BaseTool):
    @property
    def name(self): return "/compare_offers"
    @property
    def description(self): return "مقارنة عروض أسعار من صور"
    @property
    def cost(self): return 5
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        # user_input = "Image1_URL | Image2_URL | Image3_URL"
        # In production: OCR each, extract prices, compare
        prompt = f"Compare these price offers and recommend the best deal: {user_input}"
        output = await llm_client.generate(
            prompt,
            provider="nvidia",
            model=settings.NVIDIA_GENERAL_MODEL,
            system_prompt="You are a price comparison expert. Highlight best value."
        )
        return {"status": "success", "output": f"💰 Price Comparison:\n{output}", "tokens_deducted": self.cost}


class TranslateVoiceTool(BaseTool):
    @property
    def name(self): return "/translate_voice"
    @property
    def description(self): return "ترجمة فويس نوت لنص عربي"
    @property
    def cost(self): return 5
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        # user_input = voice note URL (English)
        # In production: Canary-1B ASR + Translation
        
        # Simulate ASR
        english_text = f"[English audio transcribed from: {user_input}]"
        
        # Translate to Egyptian Arabic
        prompt = f"Translate this to Egyptian Arabic: {english_text}"
        output = await llm_client.generate(prompt, provider="auto")
        
        return {"status": "success", "output": f"🌍 Translation:\n{output}", "tokens_deducted": self.cost}
