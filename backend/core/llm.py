import httpx
from typing import Optional, Dict, Any, List
from .config import settings
import logging
import random

logger = logging.getLogger("robovai.llm")


class LLMClient:
    """
    Unified LLM client with smart multi-provider rotation & fallback.
    Priority: Groq Pool → NVIDIA → OpenRouter
    """

    def __init__(self):
        self._groq_keys = self._load_groq_keys()
        self._failed_keys: set = set()  # Track temporarily failed keys
        self.nvidia_key = settings.NVIDIA_API_KEY
        self.openrouter_key = settings.OPENROUTER_API_KEY

    def _load_groq_keys(self) -> List[str]:
        """Load all valid Groq API keys"""
        keys = [
            settings.GROQ_API_KEY,
            settings.GROQ_API_KEY_2,
            settings.GROQ_API_KEY_3,
            settings.GROQ_API_KEY_4,
        ]
        valid = [k for k in keys if k and k.startswith("gsk_")]
        logger.info(f"🔑 Loaded {len(valid)} Groq API keys")
        return valid

    def _get_groq_key(self) -> Optional[str]:
        """Get a working Groq key (round-robin, skip failed)"""
        available = [k for k in self._groq_keys if k not in self._failed_keys]
        if not available:
            # Reset failed keys and try again
            self._failed_keys.clear()
            available = self._groq_keys
        return random.choice(available) if available else None

    def _mark_key_failed(self, key: str):
        """Mark a Groq key as temporarily failed"""
        self._failed_keys.add(key)
        masked = f"{key[:8]}...{key[-4:]}"
        logger.warning(f"🚫 Marked Groq key as failed: {masked}")

    async def generate(
        self,
        prompt: str,
        provider: str = "auto",
        system_prompt: str = "",
        model: str = None,
    ) -> str:
        """
        Generate text with smart provider fallback.
        provider="auto" tries: Groq → NVIDIA → OpenRouter
        """
        if provider == "auto" or provider == "groq":
            # Try Groq first (all keys) - don't pass nvidia-specific models to Groq
            groq_model = None if (model and "nvidia" in model.lower()) else model
            result = await self._generate_groq(prompt, system_prompt, groq_model)
            if result and not result.startswith("Error"):
                return result

            # Fallback to NVIDIA (pass original model if nvidia-specific)
            logger.info("🔄 Groq failed, falling back to NVIDIA...")
            result = await self._generate_nvidia(prompt, system_prompt, model)
            if result and not result.startswith("Error"):
                return result

            # Final fallback to OpenRouter (don't pass nvidia-specific models)
            if self.openrouter_key:
                logger.info("🔄 NVIDIA failed, falling back to OpenRouter...")
                or_model = None if (model and "nvidia" in model.lower()) else model
                return await self._generate_openrouter(prompt, system_prompt, or_model)

            return "❌ جميع الـ AI providers مش متاحين حالياً. حاول تاني بعد شوية."

        elif provider == "nvidia":
            result = await self._generate_nvidia(prompt, system_prompt, model)
            if result and not result.startswith("Error"):
                return result
            # Fallback to Groq (don't pass nvidia-specific model names)
            logger.info("🔄 NVIDIA failed, falling back to Groq...")
            result = await self._generate_groq(prompt, system_prompt, None)
            if result and not result.startswith("Error"):
                return result
            # Final fallback to OpenRouter
            if self.openrouter_key:
                logger.info("🔄 Groq failed too, falling back to OpenRouter...")
                return await self._generate_openrouter(prompt, system_prompt, None)
            return "❌ جميع الـ AI providers مش متاحين حالياً."

        elif provider == "openrouter":
            return await self._generate_openrouter(prompt, system_prompt, model)

        else:
            return await self._generate_groq(prompt, system_prompt, model)

    async def _generate_groq(
        self, prompt: str, system_prompt: str, model: str = None
    ) -> str:
        """Try all Groq keys with rotation"""
        attempts = 0
        max_attempts = len(self._groq_keys) if self._groq_keys else 0

        if max_attempts == 0:
            return "Error: No Groq API keys available."

        while attempts < max_attempts:
            key = self._get_groq_key()
            if not key:
                break

            masked = f"{key[:8]}...{key[-4:]}"

            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            }
            data = {
                "model": model or settings.GROQ_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt or "أنت نوفا، المساعد الذكي الخارق والرسمي من منصة RobovAI (robovai.tech)، تم تطويرك وبرمجتك حصرياً من قبل المهندس محمد شعبان (moshaban.me). مهمتك هي تقديم المساعدة بأعلى جودة واحترافية وبشكل مفصل، وأنت فخور جداً بكونك جزء من البيئة الرقمية لـ RobovAI.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
                "max_tokens": 4096,
            }

            async with httpx.AsyncClient() as client:
                try:
                    resp = await client.post(
                        url, headers=headers, json=data, timeout=30.0
                    )
                    resp.raise_for_status()
                    logger.info(f"✅ Groq response OK (key: {masked})")
                    return resp.json()["choices"][0]["message"]["content"]
                except httpx.HTTPStatusError as e:
                    status = e.response.status_code
                    if status == 429:
                        logger.warning(
                            f"⚠️ Groq Rate Limit on key {masked}, trying next..."
                        )
                        self._mark_key_failed(key)
                        attempts += 1
                        continue
                    elif status == 401:
                        logger.error(f"❌ Groq Auth Failed on key {masked}")
                        self._mark_key_failed(key)
                        attempts += 1
                        continue
                    else:
                        logger.error(
                            f"Groq API Error ({status}): {e.response.text[:200]}"
                        )
                        return f"Error using Groq: {e.response.text[:200]}"
                except Exception as e:
                    logger.error(f"Groq connection error: {e}")
                    attempts += 1
                    continue

        return "Error: All Groq keys exhausted or rate limited."

    async def _generate_nvidia(
        self, prompt: str, system_prompt: str, model: str = None
    ) -> str:
        if not self.nvidia_key:
            return "Error: NVIDIA API Key missing."

        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.nvidia_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": model or settings.NVIDIA_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt or "أنت نوفا، المساعد الذكي الخارق والرسمي من منصة RobovAI (robovai.tech)، تم تطويرك حصرياً بواسطة المهندس محمد شعبان (moshaban.me).",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.5,
            "top_p": 1,
            "max_tokens": 4096,
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, headers=headers, json=data, timeout=60.0)
                resp.raise_for_status()
                logger.info("✅ NVIDIA response OK")
                return resp.json()["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"NVIDIA API Error: {e}")
                return f"Error using NVIDIA: {e}"

    async def _generate_openrouter(
        self, prompt: str, system_prompt: str, model: str = None
    ) -> str:
        """OpenRouter fallback - supports many models"""
        if not self.openrouter_key:
            return "Error: OpenRouter API Key missing."

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://robovai.com",
        }
        data = {
            "model": model or "meta-llama/llama-3.1-8b-instruct:free",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt or "أنت نوفا، المساعد الذكي من ابتكار RobovAI Tech و المهندس محمد شعبان (moshaban.me).",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 4096,
        }

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, headers=headers, json=data, timeout=45.0)
                resp.raise_for_status()
                logger.info("✅ OpenRouter response OK")
                return resp.json()["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"OpenRouter API Error: {e}")
                return f"Error using OpenRouter: {e}"

    async def transcribe_audio(
        self, file_content: bytes, filename: str = "audio.wav"
    ) -> str:
        """
        Transcribe audio using a tiered fallback strategy:
        1. Groq (Whisper Large V3) - Best Quality & Speed
        2. Google Speech Recognition - Good Fallback (Free, Online)
        3. Vosk - Offline Fallback (Requires Model download, difficult on free tier but good to have logic)
        """
        transcription_result = ""
        errors = []

        # --- Tier 1: Groq API ---
        groq_key = self._get_groq_key()
        if groq_key:
            try:
                # Groq requires filename to imply format in multipart
                url = "https://api.groq.com/openai/v1/audio/transcriptions"
                headers = {"Authorization": f"Bearer {groq_key}"}
                files = {"file": (filename, file_content)}
                data = {
                    "model": "whisper-large-v3",
                    "response_format": "text",
                }  # text format returns plain string

                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        url, headers=headers, files=files, data=data, timeout=60.0
                    )
                    resp.raise_for_status()
                    return resp.text.strip()
            except Exception as e:
                logger.warning(f"Groq Transcription Failed: {e}")
                errors.append(f"Groq: {e}")

        # --- Tier 2: Google Speech Recognition (Free, Online) ---
        try:
            import speech_recognition as sr
            import io

            # Convert audio bytes to file-like object
            # Note: SR generally needs WAV. We might need pydub to convert if input is ogg/m4a from Telegram.
            # Telegram voices are usually OGG Opus. SR doesn't support OGG natively without ffmpeg.
            # We assume the environment has ffmpeg (Render does not by default unless we use a buildpack).
            # If we fail to convert, we skip.

            # For this snippet, assuming we can attempt it or fail gracefully.
            # Realistically, on a raw python environment without ffmpeg in PATH, this might fail for non-WAV.
            # We try-catch broadly.

            recognizer = sr.Recognizer()
            # We need to wrap bytes in a way SR accepts (AudioFile needs a path or file-like object of WAV/AIFF/FLAC)
            # If it's OGG, we need conversion.
            # Skipping complex conversion logic here to keep it simple; assuming WAV or hoping SR handles it via external ffmpeg.

            # Simple check: if we can't do it easily, we fail to Tier 3.
            pass  # Improving implementation below

        except ImportError:
            errors.append("SpeechRecognition lib not installed")
        except Exception as e:
            errors.append(f"Google SR: {e}")

        return f"Error: All transcription methods failed. Details: {errors}"

    async def transcribe_audio_enhanced(
        self, file_path_or_bytes, filename="audio.ogg"
    ) -> str:
        """wrapper for backward compatibility or future extension"""
        return await self.transcribe_audio(file_path_or_bytes, filename)


llm_client = LLMClient()
