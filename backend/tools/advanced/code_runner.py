"""
⚡ Code Runner Tool - Execute Python code safely
"""

from backend.tools.base import BaseTool
from typing import Dict, Any
import sys
from io import StringIO
import traceback
import re


class CodeRunnerTool(BaseTool):
    """
    تنفيذ كود Python في بيئة معزولة
    """
    
    @property
    def name(self) -> str:
        return "/run_code"
    
    @property
    def description(self) -> str:
        return "تنفيذ كود Python وإرجاع النتيجة (بيئة معزولة آمنة)"
    
    @property
    def cost(self) -> int:
        return 2
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        تنفيذ كود Python
        """
        try:
            code = user_input.strip()
            
            if not code:
                return {
                    "success": False,
                    "output": "❌ يرجى إدخال كود Python"
                }
            
            # فحص الأمان - منع الأوامر الخطرة
            dangerous_patterns = [
                r'import\s+os',
                r'import\s+subprocess',
                r'import\s+sys',
                r'__import__',
                r'eval\s*\(',
                r'exec\s*\(',
                r'open\s*\(',
                r'file\s*\(',
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    return {
                        "success": False,
                        "output": f"❌ غير مسموح باستخدام: {pattern}"
                    }
            
            # تنفيذ الكود
            output = StringIO()
            sys.stdout = output
            
            try:
                # بيئة محدودة
                safe_globals = {
                    '__builtins__': {
                        'print': print,
                        'len': len,
                        'range': range,
                        'str': str,
                        'int': int,
                        'float': float,
                        'list': list,
                        'dict': dict,
                        'tuple': tuple,
                        'set': set,
                        'sum': sum,
                        'max': max,
                        'min': min,
                        'abs': abs,
                        'round': round,
                        'sorted': sorted,
                        'enumerate': enumerate,
                        'zip': zip,
                    }
                }
                
                exec(code, safe_globals)
                result = output.getvalue()
                
                return {
                    "success": True,
                    "output": f"✅ تم التنفيذ بنجاح!\n\n```\n{result if result else 'لا يوجد مخرجات'}\n```",
                    "result": result
                }
                
            except Exception as e:
                error = traceback.format_exc()
                return {
                    "success": False,
                    "output": f"❌ خطأ في التنفيذ:\n\n```\n{error}\n```"
                }
            
            finally:
                sys.stdout = sys.__stdout__
                
        except Exception as e:
            return {
                "success": False,
                "output": f"❌ خطأ: {str(e)}"
            }
