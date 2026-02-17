from typing import Dict, Any
import os
import asyncio
import logging
import tempfile
import uuid

from .base import BaseTool
from backend.core.llm import llm_client
from backend.core.config import settings

logger = logging.getLogger(__name__)

# --- Groq Whisper helpers ---

_GROQ_KEYS: list = []


def _get_groq_keys() -> list:
    """Return all available GROQ_API_KEYs for failover."""
    global _GROQ_KEYS
    if not _GROQ_KEYS:
        _GROQ_KEYS = [
            k
            for k in [
                settings.GROQ_API_KEY,
                settings.GROQ_API_KEY_2,
                settings.GROQ_API_KEY_3,
                settings.GROQ_API_KEY_4,
            ]
            if k
        ]
    return _GROQ_KEYS


async def transcribe_audio(file_path: str, language: str = "ar") -> Dict[str, Any]:
    """
    Transcribe audio using official Groq SDK with key failover.
    Returns {"text": ..., "duration": ..., "language": ...} or raises.
    """
    from groq import Groq

    keys = _get_groq_keys()
    if not keys:
        raise RuntimeError("No Groq API keys configured")

    # Detect mime by extension
    ext = os.path.splitext(file_path)[1].lower()
    mime_map = {
        ".webm": "audio/webm",
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".ogg": "audio/ogg",
        ".m4a": "audio/mp4",
        ".mp4": "audio/mp4",
        ".flac": "audio/flac",
    }
    content_type = mime_map.get(ext, "audio/webm")
    filename = f"audio{ext}" if ext else "audio.webm"

    last_err = None
    for key in keys:
        try:
            client = Groq(api_key=key)
            with open(file_path, "rb") as f:
                transcription = await asyncio.to_thread(
                    client.audio.transcriptions.create,
                    file=(filename, f.read()),
                    model="whisper-large-v3-turbo",
                    language=language,
                    temperature=0,
                    response_format="verbose_json",
                )
            # transcription is a Groq object with .text, .duration, .language, etc.
            return {
                "text": transcription.text or "",
                "duration": getattr(transcription, "duration", None),
                "language": getattr(transcription, "language", language),
            }
        except Exception as e:
            last_err = e
            logger.warning(f"Groq key failed, trying next: {e}")
            continue

    raise RuntimeError(f"All Groq keys failed. Last error: {last_err}")


# --- TTS helper (edge-tts) ---

# Arabic-friendly voices
TTS_VOICES = {
    "ar": "ar-EG-SalmaNeural",  # Arabic female (Egypt)
    "ar-male": "ar-EG-ShakirNeural",  # Arabic male (Egypt)
    "en": "en-US-AriaNeural",  # English female
    "en-male": "en-US-GuyNeural",  # English male
}


async def synthesize_speech(
    text: str, voice: str | None = None, output_dir: str = "uploads/files"
) -> str:
    """
    Convert text to speech using edge-tts.
    Returns the path to the generated .mp3 file.
    """
    import edge_tts

    if not voice:
        # Auto-detect: if text is mostly Arabic, use Arabic voice
        arabic_chars = sum(1 for c in text if "\u0600" <= c <= "\u06ff")
        voice = TTS_VOICES["ar"] if arabic_chars > len(text) * 0.3 else TTS_VOICES["en"]

    os.makedirs(output_dir, exist_ok=True)
    filename = f"tts_{uuid.uuid4().hex[:12]}.mp3"
    filepath = os.path.join(output_dir, filename)

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filepath)

    return filepath


# --- Voice & Audio Tools ---


class VoiceNoteTool(BaseTool):
    @property
    def name(self):
        return "/voice_note"

    @property
    def description(self):
        return "تحويل فويس نوت لنص + رد ذكي"

    @property
    def cost(self):
        return 5

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        تحويل الصوت لنص باستخدام Groq Whisper API (official SDK with failover)
        user_input: مسار ملف صوتي أو نص عادي
        """
        if not user_input or len(user_input) < 5:
            return {
                "status": "success",
                "output": "🎤 استخدم زر التسجيل في الواجهة",
                "tokens_deducted": 0,
            }

        try:
            # Check if input is an audio file path
            is_file = (
                any(
                    user_input.endswith(ext)
                    for ext in (".webm", ".wav", ".mp3", ".ogg", ".m4a", ".flac")
                )
                or "/" in user_input
                or "\\" in user_input
            )

            if is_file and os.path.isfile(user_input):
                result = await transcribe_audio(user_input)
                transcribed_text = result["text"]
                duration = result.get("duration")

                if not transcribed_text.strip():
                    return {
                        "status": "success",
                        "output": "🎤 لم أسمع كلاماً واضحاً. حاول التسجيل مرة أخرى.",
                        "tokens_deducted": 0,
                    }

                # رد ذكي على ما قاله المستخدم
                reply_prompt = f"المستخدم قال بالصوت: '{transcribed_text}'. رد عليه بشكل طبيعي وودود."
                reply = await llm_client.generate(reply_prompt, provider="auto")

                dur_str = f"  ⏱️ {duration:.1f}s" if duration else ""
                output = f"""🎤 **تحويل ناجح!**{dur_str}

📝 **النص:** {transcribed_text}

💬 **الرد:** {reply}"""
                return {
                    "status": "success",
                    "output": output,
                    "tokens_deducted": self.cost,
                }

            else:
                # نص عادي ← رد مباشر
                output = await llm_client.generate(user_input, provider="auto")
                return {
                    "status": "success",
                    "output": output,
                    "tokens_deducted": self.cost,
                }

        except Exception as e:
            logger.error(f"VoiceNoteTool error: {e}", exc_info=True)
            return {
                "status": "error",
                "output": f"❌ خطأ في معالجة الصوت: {str(e)}",
                "tokens_deducted": 0,
            }


class TtsCustomTool(BaseTool):
    @property
    def name(self):
        return "/tts_custom"

    @property
    def description(self):
        return "تحويل نص لصوت (عربي / إنجليزي)"

    @property
    def cost(self):
        return 3

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        Real TTS using edge-tts.
        user_input: النص المراد تحويله لصوت (optionally: text | voice_key)
        """
        if not user_input or not user_input.strip():
            return {
                "status": "error",
                "output": "❌ أرسل النص المراد تحويله لصوت",
                "tokens_deducted": 0,
            }

        try:
            parts = user_input.split("|", 1)
            text = parts[0].strip()
            voice_key = parts[1].strip() if len(parts) > 1 else None
            voice = TTS_VOICES.get(voice_key) if voice_key else None

            filepath = await synthesize_speech(text, voice=voice)
            filename = os.path.basename(filepath)
            audio_url = f"/uploads/files/{filename}"

            return {
                "status": "success",
                "output": f"🔊 **تم إنشاء الصوت!**\n\n🎧 [اسمع الصوت]({audio_url})\n\n📝 النص: {text[:100]}{'…' if len(text) > 100 else ''}",
                "audio_url": audio_url,
                "tokens_deducted": self.cost,
            }
        except Exception as e:
            logger.error(f"TTS error: {e}", exc_info=True)
            return {
                "status": "error",
                "output": f"❌ خطأ في تحويل النص لصوت: {str(e)}",
                "tokens_deducted": 0,
            }


class CleanAudioTool(BaseTool):
    @property
    def name(self):
        return "/clean_audio"

    @property
    def description(self):
        return "تحسين جودة التسجيلات الصوتية"

    @property
    def cost(self):
        return 3

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        return {
            "status": "success",
            "output": f"✨ Enhanced audio quality for: {user_input}\n[Studio-quality audio URL would be here]",
            "tokens_deducted": self.cost,
        }


class MeetingNotesTool(BaseTool):
    @property
    def name(self):
        return "/meeting_notes"

    @property
    def description(self):
        return "تفريغ الاجتماعات + Action Items"

    @property
    def cost(self):
        return 10

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """Transcribe a meeting audio file using Whisper, then summarize."""
        try:
            if os.path.isfile(user_input):
                result = await transcribe_audio(user_input)
                transcript = result["text"]
            else:
                transcript = f"[Meeting transcript from: {user_input}]"

            prompt = (
                "From this meeting transcript, provide:\n"
                "1. Summary\n2. Key decisions\n3. Action items\n\n"
                f"Transcript: {transcript}"
            )
            output = await llm_client.generate(
                prompt,
                provider="auto",
                system_prompt="You are a meeting assistant. Extract structured information in Arabic.",
            )
            return {
                "status": "success",
                "output": f"📝 Meeting Notes:\n\n{output}",
                "tokens_deducted": self.cost,
            }

        except Exception as e:
            logger.error(f"MeetingNotesTool error: {e}", exc_info=True)
            return {
                "status": "error",
                "output": f"❌ خطأ: {str(e)}",
                "tokens_deducted": 0,
            }
