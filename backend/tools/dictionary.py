"""
Dictionary Tool - قاموس الكلمات
"""
import httpx
from typing import Dict, Any
from .base import BaseTool


class DictionaryTool(BaseTool):
    """
    أداة القاموس للحصول على تعريفات الكلمات
    """
    @property
    def name(self) -> str:
        return "/dictionary"
    
    @property
    def description(self) -> str:
        return "📚 قاموس - تعريفات الكلمات، النطق، الأمثلة (إنجليزي)"
    
    @property
    def cost(self) -> int:
        return 10
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        البحث عن تعريف كلمة
        """
        
        if not user_input or len(user_input) < 2:
            return {
                "status": "success",
                "output": """📚 **القاموس الإنجليزي**

**الاستخدام:**
`/dictionary [word]`

**أمثلة:**
• `/dictionary hello`
• `/dictionary computer`
• `/dictionary beautiful`

**المعلومات المتاحة:**
✅ التعريف الكامل
✅ النطق الصوتي
✅ أمثلة الاستخدام
✅ المرادفات والأضداد
✅ أصل الكلمة

💰 التكلفة: 10 توكن
🌐 مجاني بالكامل""",
                "tokens_deducted": 0
            }
        
        try:
            word = user_input.strip().lower()
            
            # استخدام Dictionary API
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            if not data or len(data) == 0:
                return {
                    "status": "error",
                    "output": f"❌ لم أجد تعريفاً للكلمة: **{word}**",
                    "tokens_deducted": 0
                }
            
            # أخذ أول نتيجة
            entry = data[0]
            
            # النطق
            phonetic = entry.get("phonetic", "N/A")
            phonetics_list = entry.get("phonetics", [])
            audio_url = ""
            for p in phonetics_list:
                if p.get("audio"):
                    audio_url = p["audio"]
                    if not audio_url.startswith("http"):
                        audio_url = "https:" + audio_url
                    break
            
            # المعاني
            meanings = entry.get("meanings", [])
            
            output_parts = [f"📚 **{entry.get('word', word).upper()}**\n"]
            
            if phonetic:
                output_parts.append(f"**النطق:** {phonetic}")
            
            if audio_url:
                output_parts.append(f"🔊 [استمع للنطق]({audio_url})")
            
            if entry.get("origin"):
                output_parts.append(f"\n**الأصل:** {entry['origin'][:150]}...")
            
            output_parts.append("\n**المعاني:**\n")
            
            # عرض أول 3 معاني
            for i, meaning in enumerate(meanings[:3], 1):
                part_of_speech = meaning.get("partOfSpeech", "")
                definitions = meaning.get("definitions", [])
                
                output_parts.append(f"**{i}. {part_of_speech.upper()}**")
                
                # عرض أول تعريفين
                for j, definition in enumerate(definitions[:2], 1):
                    def_text = definition.get("definition", "")
                    example = definition.get("example", "")
                    
                    output_parts.append(f"   • {def_text}")
                    
                    if example:
                        output_parts.append(f"   *مثال:* \"{example}\"")
                
                output_parts.append("")
            
            output_parts.append("---\n💡 Powered by Free Dictionary API")
            
            output = "\n".join(output_parts)
            
            return {
                "status": "success",
                "output": output,
                "tokens_deducted": self.cost
            }
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {
                    "status": "error",
                    "output": f"❌ الكلمة **{user_input}** غير موجودة في القاموس",
                    "tokens_deducted": 0
                }
            return {
                "status": "error",
                "output": f"❌ خطأ في الاتصال بالقاموس: {e.response.status_code}",
                "tokens_deducted": 0
            }
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ: {str(e)}",
                "tokens_deducted": 0
            }
