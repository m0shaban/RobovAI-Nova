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

async def _run_campaign_logic(campaign_id: str, user_id: str, ai_persona: str):
    """
    Core logic for fetching, generation, and publishing pipeline.
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
        logger.error(f"Error executing logic for campaign {campaign_id}: {e}")
        raise # Reraise to trigger retry

async def run_campaign(campaign_id: str, user_id: str, ai_persona: str):
    """
    Wrapper with robust Retry Logic for the campaign pipeline.
    """
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            await _run_campaign_logic(campaign_id, user_id, ai_persona)
            return # Success
        except Exception as e:
            if attempt == max_retries:
                logger.error(f"Failed campaign {campaign_id} after {max_retries} attempts: {e}")
            else:
                logger.warning(f"Campaign {campaign_id} attempt {attempt} failed. Retrying in 60s: {e}")
                await asyncio.sleep(60)

async def reload_campaign(campaign_id: str, user_id: str = None):
    """
    Dynamically reloads a specific campaign into the running APScheduler without restarting the server.
    """
    try:
        camp = await db_client.execute(
            "SELECT id, user_id, schedule_cron, ai_persona FROM content_campaigns WHERE id = ? AND is_active = 1",
            (campaign_id,)
        )
        if camp:
            c = camp[0]
            scheduler.add_job(
                run_campaign,
                CronTrigger.from_crontab(c["schedule_cron"]),
                args=[c["id"], c["user_id"], c["ai_persona"]],
                id=f"camp_{c['id']}",
                replace_existing=True
            )
            logger.info(f"Dynamically loaded campaign {c['id']} with cron {c['schedule_cron']}")
        else:
            remove_campaign(campaign_id)
    except Exception as e:
        logger.error(f"Failed to reload campaign {campaign_id}: {e}")

def remove_campaign(campaign_id: str):
    """Removes a campaign's job from the scheduler if it exists."""
    job_id = f"camp_{campaign_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f"Removed campaign {campaign_id} from scheduler")

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
