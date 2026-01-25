"""
Color Info Tool - معلومات الألوان
"""
import httpx
from typing import Dict, Any
from .base import BaseTool


class ColorInfoTool(BaseTool):
    """
    أداة معلومات الألوان
    """
    @property
    def name(self) -> str:
        return "/color"
    
    @property
    def description(self) -> str:
        return "🎨 معلومات اللون - تفاصيل أي لون HEX"
    
    @property
    def cost(self) -> int:
        return 10
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        الحصول على معلومات عن لون
        """
        
        if not user_input or not user_input.strip():
            return {
                "status": "success",
                "output": """🎨 **Color Information**

**الاستخدام:**
`/color [hex_code]`

**أمثلة:**
• `/color FF5733` - Red-Orange
• `/color 3498DB` - Blue
• `/color 2ECC71` - Green
• `/color random` - لون عشوائي

**المعلومات المتاحة:**
✅ اسم اللون
✅ RGB, HSL, HSV
✅ الألوان المكملة
✅ معاينة اللون

💰 التكلفة: 10 توكن""",
                "tokens_deducted": 0
            }
        
        try:
            color_input = user_input.strip().replace("#", "")
            
            # إذا كان المستخدم يريد لون عشوائي
            if color_input.lower() == "random":
                url = "https://www.thecolorapi.com/random"
            else:
                url = f"https://www.thecolorapi.com/id?hex={color_input}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            hex_value = data.get("hex", {}).get("value", "")
            hex_clean = data.get("hex", {}).get("clean", "")
            name = data.get("name", {}).get("value", "Unknown")
            
            rgb = data.get("rgb", {})
            rgb_str = f"rgb({rgb.get('r', 0)}, {rgb.get('g', 0)}, {rgb.get('b', 0)})"
            
            hsl = data.get("hsl", {})
            hsl_str = f"hsl({hsl.get('h', 0)}°, {hsl.get('s', 0)}%, {hsl.get('l', 0)}%)"
            
            hsv = data.get("hsv", {})
            hsv_str = f"hsv({hsv.get('h', 0)}°, {hsv.get('s', 0)}%, {hsv.get('v', 0)}%)"
            
            # الصورة
            image_url = f"https://singlecolorimage.com/get/{hex_clean}/400x200"
            
            output = f"""🎨 **Color: {name}**

![Color Preview]({image_url})

**Hex:** `{hex_value}`
**RGB:** `{rgb_str}`
**HSL:** `{hsl_str}`
**HSV:** `{hsv_str}`

**Color Swatch:**
```
████████████████████
████████████████████
████████████████████
```

---
🎨 Powered by The Color API"""
            
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
