import httpx
from typing import Optional, Dict, Any
from .config import settings
import logging

logger = logging.getLogger("robovai.llm")

class LLMClient:
    """
    Unified client for Groq and NVIDIA NIMs.
    """
    def __init__(self):
        self.groq_key = settings.GROQ_API_KEY
        self.nvidia_key = settings.NVIDIA_API_KEY
    
    async def generate(self, prompt: str, provider: str = "groq", system_prompt: str = "", model: str = None) -> str:
        """
        Generate text using the specified provider.
        """
        if provider == "groq":
            return await self._generate_groq(prompt, system_prompt, model)
        elif provider == "nvidia":
            return await self._generate_nvidia(prompt, system_prompt, model)
        else:
            return "Error: Unknown provider"

    async def _generate_groq(self, prompt: str, system_prompt: str, model: str = None) -> str:
        if not self.groq_key:
             return "Error: Groq API Key missing."
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model or settings.GROQ_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, headers=headers, json=data, timeout=30.0)
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                logger.error(f"Groq API Error: {e.response.text}")
                return f"Error using Groq: {e.response.text}"
            except Exception as e:
                logger.error(f"Groq API Error: {e}")
                return f"Error using Groq: {e}"

    async def _generate_nvidia(self, prompt: str, system_prompt: str, model: str = None) -> str:
        if not self.nvidia_key:
             return "Error: NVIDIA API Key missing."

        url = "https://integrate.api.nvidia.com/v1/chat/completions" 
        headers = {
            "Authorization": f"Bearer {self.nvidia_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model or settings.NVIDIA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5,
            "top_p": 1,
            "max_tokens": 1024
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, headers=headers, json=data, timeout=60.0)
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"NVIDIA API Error: {e}")
                return f"Error using NVIDIA: {e}"

llm_client = LLMClient()
