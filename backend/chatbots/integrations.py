import logging
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from backend.chatbots.engine import ChatbotEngine
from backend.core.database import db_client

logger = logging.getLogger("robovai.chatbots.integrations")

router = APIRouter(
    prefix="/webhook",
    tags=["Chatbot Integrations"],
)

class WebhookPayload(BaseModel):
    message: str
    user_id: str
    user_name: str = "User"

@router.post("/{bot_id}/web")
async def web_webhook(bot_id: str, payload: WebhookPayload):
    """Simple webhook for embedding the bot in a website."""
    # Verify bot exists
    query = "SELECT id FROM user_chatbots WHERE id = ?"
    result = await db_client.execute(query, (bot_id,))
    if not result:
        raise HTTPException(status_code=404, detail="Bot not found")
        
    response_text = await ChatbotEngine.process_message(
        bot_id=bot_id,
        platform_user_id=payload.user_id,
        message=payload.message,
        platform="web",
        user_name=payload.user_name
    )
    return {"response": response_text}
