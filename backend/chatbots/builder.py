import logging
from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.core.database import db_client
from backend.core.deps import get_current_user
import uuid
from backend.chatbots.rag_engine import RAGEngine

logger = logging.getLogger("robovai.chatbots")

router = APIRouter(
    prefix="/api/chatbots",
    tags=["Chatbots"],
)

class ChatbotCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    bot_type: str = "hybrid"
    system_prompt: str
    temperature: float = 0.7

class ChatbotUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    bot_type: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None

class IntegrationCreate(BaseModel):
    platform: str
    access_token: str
    webhook_url: Optional[str] = None

class TrainBotRequest(BaseModel):
    urls: List[str]

@router.post("/", response_model=dict)
async def create_chatbot(bot: ChatbotCreate, current_user: dict = Depends(get_current_user)):
    bot_id = str(uuid.uuid4())
    user_id = str(current_user["id"])
    query = """
        INSERT INTO user_chatbots (id, user_id, name, description, bot_type, system_prompt, temperature)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    await db_client.execute(query, (bot_id, user_id, bot.name, bot.description, bot.bot_type, bot.system_prompt, bot.temperature))
    return {"id": bot_id, "message": "Chatbot created successfully"}

@router.get("/", response_model=List[dict])
async def list_chatbots(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["id"])
    query = "SELECT * FROM user_chatbots WHERE user_id = ? ORDER BY created_at DESC"
    result = await db_client.execute(query, (user_id,))
    return result if result else []

@router.get("/{bot_id}", response_model=dict)
async def get_chatbot(bot_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["id"])
    query = "SELECT * FROM user_chatbots WHERE id = ? AND user_id = ?"
    result = await db_client.execute(query, (bot_id, user_id))
    if not result:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    bot_data = dict(result[0])
    
    # get integrations
    int_query = "SELECT * FROM chatbot_integrations WHERE bot_id = ?"
    integrations = await db_client.execute(int_query, (bot_id,))
    bot_data["integrations"] = integrations if integrations else []
    
    # get crm stats
    crm_query = "SELECT COUNT(*) as total_contacts FROM crm_contacts WHERE bot_id = ?"
    crm_stats = await db_client.execute(crm_query, (bot_id,))
    bot_data["crm_stats"] = crm_stats[0] if crm_stats else {"total_contacts": 0}
    
    return bot_data

@router.put("/{bot_id}", response_model=dict)
async def update_chatbot(bot_id: str, bot_update: ChatbotUpdate, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["id"])
    query = "SELECT * FROM user_chatbots WHERE id = ? AND user_id = ?"
    result = await db_client.execute(query, (bot_id, user_id))
    if not result:
        raise HTTPException(status_code=404, detail="Chatbot not found")
        
    update_fields = []
    params = []
    for field, value in bot_update.model_dump(exclude_unset=True).items():
        update_fields.append(f"{field} = ?")
        params.append(value)
        
    if update_fields:
        params.extend([bot_id, user_id])
        update_query = f"UPDATE user_chatbots SET {', '.join(update_fields)} WHERE id = ? AND user_id = ?"
        await db_client.execute(update_query, tuple(params))
        
    return {"message": "Chatbot updated successfully"}

@router.delete("/{bot_id}", response_model=dict)
async def delete_chatbot(bot_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["id"])
    query = "DELETE FROM user_chatbots WHERE id = ? AND user_id = ?"
    await db_client.execute(query, (bot_id, user_id))
    return {"message": "Chatbot deleted successfully"}

@router.post("/{bot_id}/integrations", response_model=dict)
async def add_integration(bot_id: str, integration: IntegrationCreate, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["id"])
    # Verify ownership
    query = "SELECT id FROM user_chatbots WHERE id = ? AND user_id = ?"
    result = await db_client.execute(query, (bot_id, user_id))
    if not result:
        raise HTTPException(status_code=404, detail="Chatbot not found")
        
    int_id = str(uuid.uuid4())
    insert_query = """
        INSERT INTO chatbot_integrations (id, bot_id, platform, access_token, webhook_url)
        VALUES (?, ?, ?, ?, ?)
    """
    await db_client.execute(insert_query, (int_id, bot_id, integration.platform, integration.access_token, integration.webhook_url))
    return {"id": int_id, "message": "Integration added successfully"}

@router.get("/{bot_id}/crm", response_model=List[dict])
async def get_crm_contacts(bot_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["id"])
    # Verify ownership
    query = "SELECT id FROM user_chatbots WHERE id = ? AND user_id = ?"
    result = await db_client.execute(query, (bot_id, user_id))
    if not result:
        raise HTTPException(status_code=404, detail="Chatbot not found")
        
    crm_query = "SELECT * FROM crm_contacts WHERE bot_id = ? ORDER BY last_interaction DESC"
    contacts = await db_client.execute(crm_query, (bot_id,))
    return contacts if contacts else []

@router.post("/{bot_id}/train", response_model=dict)
async def train_chatbot(bot_id: str, request: TrainBotRequest, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["id"])
    # Verify ownership
    query = "SELECT id FROM user_chatbots WHERE id = ? AND user_id = ?"
    result = await db_client.execute(query, (bot_id, user_id))
    if not result:
        raise HTTPException(status_code=404, detail="Chatbot not found")
        
    success = await RAGEngine.ingest_urls(bot_id, request.urls)
    if success:
        return {"message": "تم تغذية البوت بالمعلومات بنجاح!"}
    else:
        raise HTTPException(status_code=500, detail="فشل في جلب وتدريب البيانات من الروابط.")
