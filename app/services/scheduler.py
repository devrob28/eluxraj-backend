from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from app.db.session import SessionLocal
from app.services.scanner import scanner
from app.core.logging import logger

# Create scheduler
scheduler = AsyncIOScheduler()

async def scheduled_market_scan():
    """Run market scan on schedule"""
    logger.info("⏰ Starting scheduled market scan...")
    
    db = SessionLocal()
    try:
        result = await scanner.scan_and_save(db)
        logger.info(f"✅ Scheduled scan complete: {result['saved']} signals saved")
        
        # Log summary
        if result['saved_signals']:
            for sig in result['saved_signals']:
                logger.info(f"   📊 {sig['symbol']}: {sig['signal_type'].upper()} (Score: {sig['score']})")
        
        return result
    except Exception as e:
        logger.error(f"❌ Scheduled scan failed: {e}")
    finally:
        db.close()

async def cleanup_expired_signals():
    """Mark expired signals"""
    logger.info("🧹 Cleaning up expired signals...")
    
    from app.models.signal import Signal
    
    db = SessionLocal()
    try:
        expired = db.query(Signal).filter(
            Signal.status == "active",
            Signal.expires_at < datetime.utcnow()
        ).all()
        
        for signal in expired:
            signal.status = "expired"
            logger.info(f"   Expired: {signal.symbol} (ID: {signal.id})")
        
        db.commit()
        logger.info(f"✅ Marked {len(expired)} signals as expired")
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")
    finally:
        db.close()

def start_scheduler():
    """Start the background scheduler"""
    
    # Scan markets every hour
    scheduler.add_job(
        scheduled_market_scan,
        trigger=IntervalTrigger(hours=1),
        id="market_scan_hourly",
        name="Hourly Market Scan",
        replace_existing=True
    )
    
    # Also scan at specific times (market open/close)
    # 9:30 AM ET (14:30 UTC) - US market open
    scheduler.add_job(
        scheduled_market_scan,
        trigger=CronTrigger(hour=14, minute=30),
        id="market_scan_us_open",
        name="US Market Open Scan",
        replace_existing=True
    )
    
    # 4:00 PM ET (21:00 UTC) - US market close
    scheduler.add_job(
        scheduled_market_scan,
        trigger=CronTrigger(hour=21, minute=0),
        id="market_scan_us_close",
        name="US Market Close Scan",
        replace_existing=True
    )
    
    # Cleanup expired signals every 6 hours
    scheduler.add_job(
        cleanup_expired_signals,
        trigger=IntervalTrigger(hours=6),
        id="cleanup_expired",
        name="Cleanup Expired Signals",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("📅 Scheduler started!")
    logger.info("   - Market scan: Every hour")
    logger.info("   - US market open scan: 9:30 AM ET")
    logger.info("   - US market close scan: 4:00 PM ET")
    logger.info("   - Cleanup: Every 6 hours")

def stop_scheduler():
    """Stop the scheduler"""
    scheduler.shutdown()
    logger.info("📅 Scheduler stopped")

def get_scheduled_jobs():
    """Get list of scheduled jobs"""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
        })
    return jobs
