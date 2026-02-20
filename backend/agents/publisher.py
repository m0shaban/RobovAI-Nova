import logging
from backend.core.database import db_client
import uuid
import httpx
import os

logger = logging.getLogger("robovai.agents.publisher")

async def publish_to_facebook(access_token: str, page_id: str, content: str) -> bool:
    url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
    payload = {"message": content, "access_token": access_token}
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(url, data=payload)
            if res.status_code in [200, 201]:
                logger.info("Successfully published to Facebook Page.")
                return True
            else:
                logger.error(f"Facebook API Error: {res.text}")
                return False
    except Exception as e:
        logger.error(f"Facebook Publisher Exception: {e}")
        return False

async def publish_to_twitter(bearer_token: str, content: str) -> bool:
    url = "https://api.twitter.com/2/tweets"
    headers = {"Authorization": f"Bearer {bearer_token}", "Content-Type": "application/json"}
    payload = {"text": content}
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(url, json=payload, headers=headers)
            if res.status_code in [200, 201]:
                logger.info("Successfully published to Twitter.")
                return True
            else:
                logger.error(f"Twitter API Error: {res.text}")
                return False
    except Exception as e:
        logger.error(f"Twitter Publisher Exception: {e}")
        return False

async def publish_content(campaign_id: str, user_id: str, content: str) -> bool:
    """
    Publishes the generated content to connected platforms.
    Fetches user tokens from the database if available.
    """
    try:
        log_id = str(uuid.uuid4())
        logger.info(f"Publishing intent for campaign {campaign_id}")
        
        # 1. Check if user has connected socials in their profile (simulated query)
        # In full prod, query a `user_social_tokens` table.
        fb_token = os.getenv("TEST_FB_TOKEN") # Fallback to env for testing
        fb_page = os.getenv("TEST_FB_PAGE_ID")
        
        status = "published_to_db_only"
        
        if fb_token and fb_page:
            success = await publish_to_facebook(fb_token, fb_page, content)
            if success:
                status = "published_to_facebook"
        
        # 2. Archive to logs
        query = """
            INSERT INTO agent_publishing_logs (id, campaign_id, user_id, content, status)
            VALUES (?, ?, ?, ?, ?)
        """
        try:
            await db_client.execute(query, (log_id, campaign_id, user_id, content, status))
        except Exception as db_err:
            logger.warning(f"Failed to log to DB: {db_err}")
            
        return True
    except Exception as e:
        logger.error(f"Error publishing content: {e}")
        return False
