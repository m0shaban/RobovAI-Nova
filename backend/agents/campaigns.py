import logging
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.core.database import db_client
from backend.main import get_current_user

logger = logging.getLogger("robovai.agents")

router = APIRouter(
    prefix="/api/agents",
    tags=["Smart Agents"],
)

class CampaignCreate(BaseModel):
    name: str
    ai_persona: str
    schedule_cron: str = "0 * * * *"

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    ai_persona: Optional[str] = None
    is_active: Optional[bool] = None
    schedule_cron: Optional[str] = None

class SourceCreate(BaseModel):
    source_type: str = "rss"
    source_url: str

@router.post("/", response_model=dict)
async def create_campaign(camp: CampaignCreate, current_user: dict = Depends(get_current_user)):
    camp_id = str(uuid.uuid4())
    user_id = str(current_user["id"])
    query = """
        INSERT INTO content_campaigns (id, user_id, name, ai_persona, schedule_cron)
        VALUES (?, ?, ?, ?, ?)
    """
    await db_client.execute(query, (camp_id, user_id, camp.name, camp.ai_persona, camp.schedule_cron))
    return {"id": camp_id, "message": "Campaign created successfully"}

@router.get("/", response_model=List[dict])
async def list_campaigns(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["id"])
    query = "SELECT * FROM content_campaigns WHERE user_id = ? ORDER BY created_at DESC"
    result = await db_client.execute(query, (user_id,))
    return result if result else []

@router.get("/{campaign_id}", response_model=dict)
async def get_campaign(campaign_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["id"])
    query = "SELECT * FROM content_campaigns WHERE id = ? AND user_id = ?"
    result = await db_client.execute(query, (campaign_id, user_id))
    if not result:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    camp_data = dict(result[0])
    
    # get sources
    src_query = "SELECT * FROM content_sources WHERE campaign_id = ?"
    sources = await db_client.execute(src_query, (campaign_id,))
    camp_data["sources"] = sources if sources else []
    
    return camp_data

@router.put("/{campaign_id}", response_model=dict)
async def update_campaign(campaign_id: str, camp_update: CampaignUpdate, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["id"])
    query = "SELECT id FROM content_campaigns WHERE id = ? AND user_id = ?"
    result = await db_client.execute(query, (campaign_id, user_id))
    if not result:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    update_fields = []
    params = []
    for field, value in camp_update.model_dump(exclude_unset=True).items():
        update_fields.append(f"{field} = ?")
        params.append(value)
        
    if update_fields:
        params.extend([campaign_id, user_id])
        update_query = f"UPDATE content_campaigns SET {', '.join(update_fields)} WHERE id = ? AND user_id = ?"
        await db_client.execute(update_query, tuple(params))
        
    return {"message": "Campaign updated successfully"}

@router.delete("/{campaign_id}", response_model=dict)
async def delete_campaign(campaign_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["id"])
    query = "DELETE FROM content_campaigns WHERE id = ? AND user_id = ?"
    await db_client.execute(query, (campaign_id, user_id))
    return {"message": "Campaign deleted successfully"}

@router.post("/{campaign_id}/sources", response_model=dict)
async def add_source(campaign_id: str, source: SourceCreate, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["id"])
    # Verify ownership
    query = "SELECT id FROM content_campaigns WHERE id = ? AND user_id = ?"
    result = await db_client.execute(query, (campaign_id, user_id))
    if not result:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    src_id = str(uuid.uuid4())
    insert_query = """
        INSERT INTO content_sources (id, campaign_id, source_type, source_url)
        VALUES (?, ?, ?, ?)
    """
    await db_client.execute(insert_query, (src_id, campaign_id, source.source_type, source.source_url))
    return {"id": src_id, "message": "Source added successfully"}

@router.delete("/{campaign_id}/sources/{source_id}", response_model=dict)
async def delete_source(campaign_id: str, source_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["id"])
    # Verify ownership
    query = "SELECT id FROM content_campaigns WHERE id = ? AND user_id = ?"
    result = await db_client.execute(query, (campaign_id, user_id))
    if not result:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    del_query = "DELETE FROM content_sources WHERE id = ? AND campaign_id = ?"
    await db_client.execute(del_query, (source_id, campaign_id))
    return {"message": "Source deleted successfully"}
