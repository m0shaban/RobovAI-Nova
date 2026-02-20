import logging
import uuid
import os
from datetime import datetime
from backend.core.database import db_client
from backend.core.llm import llm_client
from backend.chatbots.rag_engine import RAGEngine

logger = logging.getLogger("robovai.chatbots.engine")

class ChatbotEngine:
    @staticmethod
    async def process_message(bot_id: str, platform_user_id: str, message: str, platform: str = "web", user_name: str = "User") -> str:
        """Process incoming messages for a specific custom bot"""
        # 1. Fetch Bot Configuration
        query = "SELECT * FROM user_chatbots WHERE id = ?"
        bot_result = await db_client.execute(query, (bot_id,))
        if not bot_result:
            logger.error(f"Bot {bot_id} not found")
            return "مرحباً! يبدو أن هذا البوت غير متاح حالياً."
        
        bot_config = bot_result[0]
        
        # 2. Update CRM / User Profile
        await ChatbotEngine._update_crm(bot_id, platform_user_id, platform, user_name)
        
        # 3. Handle Message based on bot_type
        bot_type = bot_config.get("bot_type", "hybrid")
        system_prompt = bot_config.get("system_prompt", "أنت مساعد ذكي.")
        temperature = bot_config.get("temperature", 0.7)
        
        if bot_type == "rules_only":
            return ChatbotEngine._process_rules(message)
        elif bot_type == "ai_only":
            return await ChatbotEngine._process_ai(bot_id, system_prompt, message, temperature)
        else: # Hybrid
            fallback_ai = await ChatbotEngine._process_ai(bot_id, system_prompt, message, temperature)
            return fallback_ai
            
    @staticmethod
    async def _update_crm(bot_id: str, platform_user_id: str, platform: str, name: str):
        # Check if user exists
        query = "SELECT id FROM crm_contacts WHERE bot_id = ? AND platform_user_id = ?"
        result = await db_client.execute(query, (bot_id, platform_user_id))
        
        now_str = datetime.now().isoformat()
        if result:
            # Update existing
            contact_id = result[0]["id"]
            update_q = "UPDATE crm_contacts SET interactions_count = interactions_count + 1, last_interaction = ? WHERE id = ?"
            await db_client.execute(update_q, (now_str, contact_id))
        else:
            # Insert new
            contact_id = str(uuid.uuid4())
            insert_q = "INSERT INTO crm_contacts (id, bot_id, platform_user_id, name, interactions_count, last_interaction) VALUES (?, ?, ?, ?, 1, ?)"
            await db_client.execute(insert_q, (contact_id, bot_id, platform_user_id, name, now_str))

    @staticmethod
    def _process_rules(message: str) -> str:
        # A basic static rules engine. In a full system, this would fetch from a `bot_rules` table.
        rules = {
            "hello": "مرحباً بك! كيف يمكنني مساعدتك؟",
            "مرحبا": "أهلاً بك! تفضل، كيف يمكنني خدمتك؟",
            "price": "أسعارنا تختلف حسب الباقة، يمكنك الاطلاع عليها من قائمة الأسعار.",
            "سعر": "أسعارنا تبدأ من 10 دولار، وتتغير حسب الخطة المختارة.",
            "help": "يسعدني الإجابة على استفساراتك حول خدماتنا وحلولنا الذكية.",
            "مساعدة": "أنا هنا لمساعدتك، ما هو سؤالك؟"
        }
        for key, response in rules.items():
            if key in message.lower():
                return response
        return "عذراً، لم أجد إجابة مبرمجة مسبقاً لهذا السؤال في خوارزمياتي."
        
    @staticmethod
    async def _process_ai(bot_id: str, system_prompt: str, message: str, temperature: float) -> str:
        try:
            # 1. Retrieve Context from FAISS (RAG)
            context = await RAGEngine.retrieve_context(bot_id, message)
            
            enhanced_system_prompt = system_prompt
            if context:
                enhanced_system_prompt += f"\n\n--- معلومات إضافية عن الشركة أو النظام يجب الاعتماد عليها للإجابة ---\n{context}"
                
            return await llm_client.generate(
                prompt=message,
                system_prompt=enhanced_system_prompt,
                provider="auto"
            )
        except Exception as e:
            logger.error(f"LLM API Error in Custom Bot: {e}")
            return "عذراً، حدث خطأ أثناء الاتصال بمحرك الذكاء الاصطناعي."
