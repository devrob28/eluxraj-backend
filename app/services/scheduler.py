"""
Background Scheduler
Run periodic jobs like alert monitoring
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timezone
from app.core.logging import logger
from app.db.session import SessionLocal


scheduler = AsyncIOScheduler()


async def check_alerts_job():
    """Job to check and trigger alerts"""
    from app.services.alert_monitor import alert_monitor
    
    db = SessionLocal()
    try:
        result = await alert_monitor.run_alert_check(db)
        logger.info(f"Alert job completed: {result['triggered_count']} triggered")
    except Exception as e:
        logger.error(f"Alert job error: {e}")
    finally:
        db.close()


async def generate_weekly_brief_job():
    """Job to generate weekly brief on Sundays"""
    from app.services.weekly_brief import weekly_brief_service
    
    # Only run on Sundays
    if datetime.now(timezone.utc).weekday() != 6:
        return
    
    db = SessionLocal()
    try:
        await weekly_brief_service.generate_weekly_brief(db)
        logger.info("Weekly brief generated")
    except Exception as e:
        logger.error(f"Weekly brief job error: {e}")
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler"""
    # Check alerts every 2 minutes
    scheduler.add_job(
        check_alerts_job,
        IntervalTrigger(minutes=2),
        id="alert_check",
        name="Check price alerts",
        replace_existing=True
    )
    
    # Check for weekly brief generation daily at 00:00 UTC
    scheduler.add_job(
        generate_weekly_brief_job,
        IntervalTrigger(hours=24),
        id="weekly_brief",
        name="Generate weekly brief",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Background scheduler started")


def stop_scheduler():
    """Stop the scheduler"""
    scheduler.shutdown()
    logger.info("Background scheduler stopped")
