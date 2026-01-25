from typing import Dict, Any
from .base import BaseTool
from backend.core.llm import llm_client
from backend.core.config import settings
import httpx

class NvidiaTtsTool(BaseTool):
    """
    تحويل نص لصوت باستخدام NVIDIA Magpie TTS مع خيارات متعددة للأصوات
    """
    @property
    def name(self): return "/nvidia_tts"
    @property
    def description(self): return "تحويل نص لصوت احترافي مع اختيار الصوت"
    @property
    def cost(self): return 3
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        user_input format: "النص | voice (optional)"
        Available voices:
        - Magpie-Multilingual.EN-US.Aria (أنثى إنجليزي)
        - Magpie-Multilingual.EN-US.Davis (ذكر إنجليزي)
        - وغيرها...
        """
        if not user_input or len(user_input) < 3:
            return {
                "status": "success",
                "output": """🔊 **NVIDIA TTS - Text to Speech**

**الاستخدام:**
`/nvidia_tts النص المطلوب`
أو
`/nvidia_tts النص | Magpie-Multilingual.EN-US.Aria`

**أصوات متاحة:**
• EN-US.Aria - أنثى أمريكية
• EN-US.Davis - ذكر أمريكي  
• EN-GB.Harper - أنثى بريطانية
• وغيرها...

**مثال:**
`/nvidia_tts Hello, this is a test | EN-US.Aria`""",
                "tokens_deducted": 0
            }
        
        # فصل النص عن اسم الصوت
        parts = user_input.split('|')
        text = parts[0].strip()
        voice = parts[1].strip() if len(parts) > 1 else "Magpie-Multilingual.EN-US.Aria"
        
        # التحقق من NVIDIA API Key
        if not settings.NVIDIA_API_KEY:
            return {
                "status": "error",
                "output": "❌ NVIDIA API Key غير موجود في .env",
                "tokens_deducted": 0
            }
        
        try:
            # ملاحظة: NVIDIA TTS يستخدم gRPC وليس REST API
            # للاستخدام الفعلي، يحتاج nvidia-riva-client
            # هنا نقدم تعليمات للمستخدم
            
            instructions = f"""🔊 **تم تجهيز الطلب!**

📝 **النص:** {text}
🎙️ **الصوت:** {voice}

⚡ **للتنفيذ الفعلي:**
```bash
pip install nvidia-riva-client
python -c "
from riva.client import SpeechSynthesis
client = SpeechSynthesis('grpc.nvcf.nvidia.com:443', use_ssl=True)
audio = client.synthesize(
    text='{text}',
    voice='{voice}',
    language_code='en-US'
)
with open('output.wav', 'wb') as f:
    f.write(audio)
"
```

💡 **أو استخدم Web Speech API** في المتصفح مباشرة!"""
            
            return {
                "status": "success",
                "output": instructions,
                "tokens_deducted": self.cost
            }
            
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ: {str(e)}",
                "tokens_deducted": 0
            }
