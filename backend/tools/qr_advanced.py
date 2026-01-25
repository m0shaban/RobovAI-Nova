"""
Enhanced QR Code Tool - إنشاء رموز QR متقدمة (Fixed)
"""
import urllib.parse
from typing import Dict, Any
from .base import BaseTool
import re


class QRAdvancedTool(BaseTool):
    """
    أداة إنشاء رموز QR متقدمة مع ألوان وأحجام مخصصة
    """
    @property
    def name(self) -> str:
        return "/qr_advanced"
    
    @property
    def description(self) -> str:
        return "📱 QR Code متقدم - رموز QR ملونة وقابلة للتخصيص"
    
    @property
    def cost(self) -> int:
        return 10
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        إنشاء رمز QR متقدم
        """
        
        if not user_input or len(user_input) < 2:
            return {
                "status": "success",
                "output": """📱 **QR Code متقدم**

**الاستخدام:**
`/qr_advanced النص الذي تريده`
أو
`/qr_advanced "نص طويل هنا" 400 blue`

**أمثلة:**
• `/qr_advanced https://example.com`
• `/qr_advanced بسم الله الرحمن الرحيم`
• `/qr_advanced Hello World 300 blue`

**الألوان المتاحة:**
• `blue` - أزرق
• `red` - أحمر
• `green` - أخضر
• `purple` - بنفسجي
• `orange` - برتقالي

**المميزات:**
✅ رموز QR ملونة
✅ أحجام مخصصة
✅ دعم العربية والإنجليزية
✅ مجاني بالكامل

💰 التكلفة: 10 توكن""",
                "tokens_deducted": 0
            }
        
        try:
            # Default values
            size = "300"
            color = "000000"  # Black
            text = user_input.strip()
            
            # Remove brackets if present
            text = text.replace('[', '').replace(']', '')
            
            # Color mapping
            color_map = {
                "blue": "0066CC",
                "red": "CC0000",
                "green": "00CC00",
                "purple": "6600CC",
                "orange": "FF8C00",
                "black": "000000",
                "navy": "000080",
                "teal": "008080",
                "cyan": "00CCCC",
                "pink": "CC0066"
            }
            
            # Check if last words are size/color
            parts = text.split()
            
            # Check for color at the end
            if len(parts) >= 2 and parts[-1].lower() in color_map:
                color = color_map[parts[-1].lower()]
                parts = parts[:-1]
                text = ' '.join(parts)
            
            # Check for size
            if len(parts) >= 2 and parts[-1].isdigit():
                size = parts[-1]
                if int(size) < 100:
                    size = "300"
                if int(size) > 1000:
                    size = "1000"
                parts = parts[:-1]
                text = ' '.join(parts)
            
            # Build URL with proper encoding
            base_url = "https://api.qrserver.com/v1/create-qr-code/"
            encoded_text = urllib.parse.quote(text, safe='')
            
            qr_url = f"{base_url}?size={size}x{size}&data={encoded_text}&color={color}&charset-source=UTF-8"
            
            output = f"""📱 **تم إنشاء رمز QR!**

**المحتوى:** {text}
**الحجم:** {size}x{size} بكسل
**اللون:** #{color}

**رمز QR:**
![QR Code]({qr_url})

**الرابط المباشر:**
{qr_url}

---
💡 امسح الرمز بكاميرا هاتفك!
🎨 جرب: `/qr_advanced النص 400 blue`"""
            
            return {
                "status": "success",
                "output": output,
                "tokens_deducted": self.cost
            }
            
        except Exception as e:
            return {
                "status": "error",
                "output": f"❌ خطأ: {str(e)}",
                "tokens_deducted": 0
            }
