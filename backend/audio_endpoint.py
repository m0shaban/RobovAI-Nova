from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
import tempfile
import os

@app.post("/webhook_audio")
async def handle_audio_webhook(
    audio: UploadFile = File(...),
    user_id: str = Form(...),
    platform: str = Form(...)
):
    """
    نقطة نهاية منفصلة لاستقبال ملفات الصوت
    """
    logger.info(f"Received audio file from {platform}")
    
    try:
        # حفظ الملف مؤقتاً
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # استدعاء أداة voice_note مع مسار الملف
        from backend.tools.registry import ToolRegistry
        tool_class = ToolRegistry.get_tool('/voice_note')
        
        if tool_class:
            tool = tool_class()
            result = await tool.execute(temp_path, user_id)
            
            # حذف الملف المؤقت
            os.unlink(temp_path)
            
            response = result.get('output', 'تم معالجة الصوت')
            return {"status": "success", "response": response, "output": response}
        else:
            os.unlink(temp_path)
            return {"status": "error", "message": "Voice tool not found"}
            
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        return {"status": "error", "message": str(e), "response": f"❌ خطأ: {str(e)}"}
