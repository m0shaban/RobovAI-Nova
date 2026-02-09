from typing import Dict, Any
from .base import BaseTool
from backend.core.llm import llm_client
from backend.core.config import settings

# --- Voice & Audio Tools ---

class VoiceNoteTool(BaseTool):
    @property
    def name(self): return "/voice_note"
    @property
    def description(self): return "تحويل فويس نوت لنص + رد ذكي"
    @property
    def cost(self): return 5
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        تحويل الصوت لنص باستخدام Groq Whisper API
        user_input: إما مسار ملف أو base64
        """
        import httpx
        
        if not user_input or len(user_input) < 5:
            return {
                "status": "success", 
                "output": "🎤 استخدم زر التسجيل في الواجهة",
                "tokens_deducted": 0
            }
        
        # التحقق من Groq API Key
        if not settings.GROQ_API_KEY:
            return {
                "status": "error",
                "output": "❌ Groq API Key غير موجود",
                "tokens_deducted": 0
            }
        
        try:
            # التعامل مع ملف حقيقي (من الواجهة)
            if user_input.endswith('.webm') or user_input.endswith('.wav') or '/' in user_input or '\\' in user_input:
                # مسار ملف
                async with httpx.AsyncClient(timeout=30.0) as client:
                    with open(user_input, 'rb') as audio_file:
                        files = {
                            'file': ('audio.webm', audio_file, 'audio/webm')
                        }
                        data = {
                            'model': 'whisper-large-v3-turbo',
                            'language': 'ar',
                            'response_format': 'json',
                            'temperature': 0.0
                        }
                        headers = {
                            'Authorization': f'Bearer {settings.GROQ_API_KEY}'
                        }
                        
                        response = await client.post(
                            'https://api.groq.com/openai/v1/audio/transcriptions',
                            files=files,
                            data=data,
                            headers=headers
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            transcribed_text = result.get('text', '')
                            
                            # رد ذكي
                            reply_prompt = f"المستخدم قال: '{transcribed_text}'. رد عليه بود."
                            reply = await llm_client.generate(reply_prompt, provider="auto")
                            
                            output = f"""🎤 **تحويل ناجح!**

📝 **النص:** {transcribed_text}

💬 **الرد:** {reply}"""
                        else:
                            output = f"❌ خطأ Whisper: {response.status_code}\n{response.text}"
            
            else:
                # نص عادي
                output = await llm_client.generate(user_input, provider="auto")
            
            return {"status": "success", "output": output, "tokens_deducted": self.cost}
            
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ: {str(e)}",
                "tokens_deducted": 0
            }


class TtsCustomTool(BaseTool):
    @property
    def name(self): return "/tts_custom"
    @property
    def description(self): return "تحويل نص لصوت بصوتك الخاص"
    @property
    def cost(self): return 5
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        # user_input format: "Text to speak | Voice sample URL"
        # In production: Use magpie-tts-zeroshot
        parts = user_input.split("|")
        if len(parts) < 2:
            return {"status": "error", "output": "Format: Text | Voice Sample URL"}
        
        text, voice_sample = parts[0].strip(), parts[1].strip()
        
        # Simulate TTS
        return {
            "status": "success", 
            "output": f"🔊 Generated audio for: '{text}' using voice from {voice_sample}\n[Audio URL would be here in production]",
            "tokens_deducted": self.cost
        }


class CleanAudioTool(BaseTool):
    @property
    def name(self): return "/clean_audio"
    @property
    def description(self): return "تحسين جودة التسجيلات الصوتية"
    @property
    def cost(self): return 3
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        # user_input = audio URL
        # In production: nvidia/background-noise-removal + studiovoice
        return {
            "status": "success",
            "output": f"✨ Enhanced audio quality for: {user_input}\n[Studio-quality audio URL would be here]",
            "tokens_deducted": self.cost
        }


class MeetingNotesTool(BaseTool):
    @property
    def name(self): return "/meeting_notes"
    @property
    def description(self): return "تفريغ الاجتماعات + Action Items"
    @property
    def cost(self): return 10
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        # user_input = meeting recording URL
        # Pipeline: ASR → Summarization → Extract Action Items
        
        # Simulate ASR
        transcript = f"[Meeting transcript from: {user_input}]"
        
        # Summarize + Extract actions
        prompt = f"From this meeting transcript, provide:\n1. Summary\n2. Key decisions\n3. Action items\n\nTranscript: {transcript}"
        output = await llm_client.generate(
            prompt, 
            provider="nvidia",
            model=settings.NVIDIA_GENERAL_MODEL,
            system_prompt="You are a meeting assistant. Extract structured information."
        )
        
        return {"status": "success", "output": f"📝 Meeting Notes:\n\n{output}", "tokens_deducted": self.cost}
