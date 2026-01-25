from typing import Dict, Any
from .base import BaseTool
import io
import logging

logger = logging.getLogger("robovai.tools.img")

try:
    import qrcode
    from PIL import Image, ImageOps, ImageFilter
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

class QRCodeTool(BaseTool):
    @property
    def name(self) -> str:
        return "/qr_create"

    @property
    def description(self) -> str:
        return "Generates a QR Code from text/URL."

    @property
    def cost(self) -> int:
        return 0

    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        if not PILLOW_AVAILABLE:
            return {"status": "error", "output": "⚠️ Missing dependency: pillow/qrcode. Please install them."}
        
        if not user_input.strip():
            return {"status": "error", "output": "❌ Please provide text for the QR code."}

        try:
            # Generate QR
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(user_input.strip())
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save to bytes
            byte_io = io.BytesIO()
            img.save(byte_io, format='PNG')
            byte_io.seek(0)
            
            return {
                "status": "success",
                "output": "📱 **تم إنشاء رمز QR بنجاح.**",
                "file_content": byte_io.getvalue(),
                "file_name": "qrcode.png",
                "tokens_deducted": 0
            }
        except Exception as e:
            return {"status": "error", "output": f"❌ QR Error: {e}"}

class ImageProcessTool(BaseTool):
    @property
    def name(self) -> str:
        return "/image_edit"

    @property
    def description(self) -> str:
        return "Simple image editing (BW, Invert, Resize)."

    @property
    def cost(self) -> int:
        return 0

    async def execute(self, user_input: str, user_id: str, file_content: bytes = None) -> Dict[str, Any]:
        """
        Input: "grayscale" or "invert" or "resize"
        """
        if not PILLOW_AVAILABLE:
             return {"status": "error", "output": "⚠️ Missing dependency: pillow."}
        
        if not file_content:
             return {"status": "error", "output": "❌ No image provided."}

        mode = user_input.strip().lower()
        
        try:
            image = Image.open(io.BytesIO(file_content))
            
            if "gray" in mode or "bw" in mode:
                image = ImageOps.grayscale(image)
                msg = "⚫⚪ تم تحويل الصورة للأبيض والأسود."
            
            elif "invert" in mode or "neg" in mode:
                # Invert needs RGB usually
                if image.mode == 'RGBA':
                    r,g,b,a = image.split()
                    rgb_image = Image.merge('RGB', (r,g,b))
                    inverted_image = ImageOps.invert(rgb_image)
                    r2,g2,b2 = inverted_image.split()
                    image = Image.merge('RGBA', (r2,g2,b2,a))
                else:
                    image = ImageOps.invert(image)
                msg = "🔄 تم عكس ألوان الصورة (Negative)."
                
            elif "blur" in mode:
                image = image.filter(ImageFilter.BLUR)
                msg = "💧 تم تمويه الصورة (Blur)."
            
            else:
                return {"status": "error", "output": "❌ Mode not supported. Use: grayscale, invert, blur."}

            # Save
            out_io = io.BytesIO()
            # Preserve format if possible or default to PNG
            fmt = image.format if image.format else 'PNG'
            image.save(out_io, format=fmt)
            
            return {
                "status": "success",
                "output": msg,
                "file_content": out_io.getvalue(),
                "file_name": f"edited.{fmt.lower()}",
                "tokens_deducted": 0
            }

        except Exception as e:
            return {"status": "error", "output": f"❌ Image Error: {e}"}
