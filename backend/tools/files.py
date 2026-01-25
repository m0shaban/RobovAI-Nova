from typing import Dict, Any, Type
from .base import BaseTool
import os
import io
import logging

logger = logging.getLogger("robovai.tools.files")

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

class PDFReaderTool(BaseTool):
    @property
    def name(self) -> str:
        return "/read_pdf"

    @property
    def description(self) -> str:
        return "Extracts text from PDF files for analysis."

    @property
    def cost(self) -> int:
        return 0

    async def execute(self, user_input: str, user_id: str, file_path: str = None, file_content: bytes = None) -> Dict[str, Any]:
        """
        Reads a PDF file and returns the text.
        Args:
            user_input: Not used directly usually.
            file_path: local path to the file.
            file_content: bytes of the file.
        """
        if not PDF_AVAILABLE:
            return {"status": "error", "output": "⚠️ Missing dependency: PyPDF2. Please install it to use this feature."}

        text = ""
        try:
            if file_content:
                reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            elif file_path and os.path.exists(file_path):
                reader = PyPDF2.PdfReader(file_path)
            else:
                return {"status": "error", "output": "No file provided."}

            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            return {
                "status": "success",
                "output": text.strip() or "⚠️ No text found in this PDF (it might be an image scan).",
                "tokens_deducted": 0
            }
        except Exception as e:
            logger.error(f"PDF Read Error: {e}")
            return {"status": "error", "output": f"Failed to read PDF: {str(e)}"}

class DocxReaderTool(BaseTool):
    @property
    def name(self) -> str:
        return "/read_docx"

    @property
    def description(self) -> str:
        return "Extracts text from Word documents."

    @property
    def cost(self) -> int:
        return 0

    async def execute(self, user_input: str, user_id: str, file_content: bytes = None) -> Dict[str, Any]:
        if not DOCX_AVAILABLE:
             return {"status": "error", "output": "⚠️ Missing dependency: python-docx. Please install it."}
        
        try:
            if not file_content:
                return {"status": "error", "output": "No file content provided."}
                
            doc = docx.Document(io.BytesIO(file_content))
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            
            return {
                "status": "success",
                "output": '\n'.join(full_text),
                "tokens_deducted": 0
            }
        except Exception as e:
            return {"status": "error", "output": f"Docx Error: {e}"}
