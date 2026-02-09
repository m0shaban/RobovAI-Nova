"""
📁 File Creator Tool - Create and save files
"""

from backend.tools.base import BaseTool
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel, Field
import os
from datetime import datetime


class FileCreatorInput(BaseModel):
    """Input schema for file creation"""
    filename: str = Field(description="File name with extension, e.g. 'page.html', 'style.css', 'data.json'")
    content: str = Field(description="The full file content to write")
    query: Optional[str] = Field(default=None, description="Optional description (not used)")


class FileCreatorTool(BaseTool):
    """
    إنشاء وحفظ ملفات (HTML, CSS, TXT, JSON, etc.)
    """
    
    @property
    def name(self) -> str:
        return "/create_file"
    
    @property
    def description(self) -> str:
        return "Create and save files. Pass 'filename' (e.g. page.html) and 'content' (the full file content)."
    
    @property
    def args_schema(self) -> Type[BaseModel]:
        return FileCreatorInput
    
    @property
    def cost(self) -> int:
        return 1
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        إنشاء ملف
        
        Format: filename.ext | content
        """
        try:
            if "|" not in user_input:
                return {
                    "success": False,
                    "output": "❌ الصيغة: اسم_الملف.امتداد | المحتوى"
                }
            
            filename, content = user_input.split("|", 1)
            filename = filename.strip()
            content = content.strip()
            
            # التحقق من الامتداد
            allowed_extensions = ['.html', '.css', '.txt', '.json', '.md', '.js', '.py']
            ext = os.path.splitext(filename)[1].lower()
            
            if ext not in allowed_extensions:
                return {
                    "success": False,
                    "output": f"❌ الامتدادات المسموحة: {', '.join(allowed_extensions)}"
                }
            
            # إنشاء المجلد
            os.makedirs("uploads/files", exist_ok=True)
            
            # إضافة timestamp للاسم لتجنب التكرار
            base_name = os.path.splitext(filename)[0]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            final_filename = f"{base_name}_{timestamp}{ext}"
            
            filepath = os.path.join("uploads/files", final_filename)
            
            # حفظ الملف
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            
            # حساب حجم الملف
            file_size = os.path.getsize(filepath)
            size_kb = file_size / 1024
            
            url = f"/uploads/files/{final_filename}"
            
            return {
                "success": True,
                "output": f"✅ تم إنشاء الملف بنجاح!\n\n📄 الاسم: {final_filename}\n💾 الحجم: {size_kb:.2f} KB\n🔗 الرابط: {url}",
                "filepath": filepath,
                "url": url,
                "filename": final_filename,
                "size_bytes": file_size
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": f"❌ خطأ في إنشاء الملف: {str(e)}"
            }
