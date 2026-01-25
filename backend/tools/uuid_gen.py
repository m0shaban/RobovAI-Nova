"""
UUID Generator Tool - مولد UUID
"""
import uuid
from typing import Dict, Any
from .base import BaseTool


class UUIDGeneratorTool(BaseTool):
    """
    أداة توليد UUID
    """
    @property
    def name(self) -> str:
        return "/uuid"
    
    @property
    def description(self) -> str:
        return "🔑 UUID - توليد معرفات فريدة"
    
    @property
    def cost(self) -> int:
        return 5
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        توليد UUID
        """
        
        try:
            # تحديد عدد الـ UUIDs المطلوبة (افتراضي: 1)
            count = 1
            if user_input and user_input.strip().isdigit():
                count = int(user_input.strip())
                count = min(count, 10)  # حد أقصى 10
            
            uuids = []
            for _ in range(count):
                # UUID v4 (عشوائي)
                new_uuid = str(uuid.uuid4())
                uuids.append(new_uuid)
            
            if count == 1:
                output = f"""🔑 **UUID Generated**

```
{uuids[0]}
```

**Format:** UUID v4 (Random)
**Length:** 36 characters

---
✨ Universally Unique Identifier"""
            else:
                uuid_list = "\n".join([f"{i+1}. `{u}`" for i, u in enumerate(uuids)])
                output = f"""🔑 **{count} UUIDs Generated**

{uuid_list}

**Format:** UUID v4 (Random)
**Length:** 36 characters each

---
✨ Universally Unique Identifiers"""
            
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
