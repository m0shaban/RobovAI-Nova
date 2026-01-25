"""
Trivia Questions Tool - أسئلة ثقافية
"""
import httpx
from typing import Dict, Any
from .base import BaseTool
import html


class TriviaTool(BaseTool):
    """
    أداة الأسئلة الثقافية
    """
    @property
    def name(self) -> str:
        return "/trivia"
    
    @property
    def description(self) -> str:
        return "🎯 أسئلة ثقافية - اختبر معلوماتك"
    
    @property
    def cost(self) -> int:
        return 10
    
    async def execute(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """
        الحصول على سؤال ثقافي عشوائي
        """
        
        try:
            url = "https://opentdb.com/api.php?amount=1&type=multiple"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
            
            if data.get("response_code") != 0:
                return {
                    "status": "error",
                    "output": "❌ فشل في الحصول على سؤال",
                    "tokens_deducted": 0
                }
            
            question_data = data["results"][0]
            
            # فك تشفير HTML entities
            question = html.unescape(question_data["question"])
            correct_answer = html.unescape(question_data["correct_answer"])
            incorrect_answers = [html.unescape(ans) for ans in question_data["incorrect_answers"]]
            category = html.unescape(question_data["category"])
            difficulty = question_data["difficulty"].capitalize()
            
            # دمج الإجابات وترتيبها
            all_answers = [correct_answer] + incorrect_answers
            
            output = f"""🎯 **Trivia Question**

**Category:** {category}
**Difficulty:** {difficulty}

**Question:**
{question}

**Options:**
A) {all_answers[0]}
B) {all_answers[1]}
C) {all_answers[2]}
D) {all_answers[3]}

**Correct Answer:**
||{correct_answer}||

---
🧠 Test your knowledge!"""
            
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
