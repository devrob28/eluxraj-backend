"""
ELUXRAJ Scheduler Service
Runs periodic tasks: portfolio scans, alert checks, data updates
"""
import asyncio
from datetime import datetime, timezone
from app.core.logging import logger


class Scheduler:
    """Simple task scheduler for periodic jobs"""
    
    def __init__(self):
        self.tasks = {}
        self.running = False
    
    def add_task(self, name: str, interval_seconds: int, func):
        """Add a periodic task"""
        self.tasks[name] = {
            "interval": interval_seconds,
            "func": func,
            "last_run": None
        }
    
    async def run_task(self, name: str):
        """Run a single task"""
        task = self.tasks.get(name)
        if not task:
            return
        
        try:
            logger.info(f"Running scheduled task: {name}")
            if asyncio.iscoroutinefunction(task["func"]):
                await task["func"]()
            else:
                task["func"]()
            task["last_run"] = datetime.now(timezone.utc)
            logger.info(f"Task {name} completed")
        except Exception as e:
            logger.error(f"Task {name} failed: {e}")
    
    async def start(self):
        """Start the scheduler loop"""
        self.running = True
        logger.info("Scheduler started")
        
        while self.running:
            now = datetime.now(timezone.utc)
            
            for name, task in self.tasks.items():
                # Check if task should run
                if task["last_run"] is None:
                    should_run = True
                else:
                    elapsed = (now - task["last_run"]).total_seconds()
                    should_run = elapsed >= task["interval"]
                
                if should_run:
                    asyncio.create_task(self.run_task(name))
            
            # Sleep before checking again
            await asyncio.sleep(60)  # Check every minute
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        logger.info("Scheduler stopped")


# Global scheduler instance
scheduler = Scheduler()


async def hourly_portfolio_scan():
    """Scan all users' watchlist assets hourly"""
    from app.db.session import SessionLocal
    from app.services.oracle import oracle
    from app.api.endpoints.alerts import check_and_trigger_alerts
    
    db = SessionLocal()
    try:
        # Get unique assets from all alert rules
        from app.api.endpoints.alerts import AlertRule
        rules = db.query(AlertRule).filter(AlertRule.is_active == True).all()
        assets = list(set(r.asset for r in rules))
        
        logger.info(f"Hourly scan: {len(assets)} assets")
        
        for asset in assets:
            try:
                signal = await oracle.generate_signal(asset)
                if signal:
                    score = signal.get("oracle_score", 50)
                    await check_and_trigger_alerts(asset, "oracle_score", score, db)
            except Exception as e:
                logger.error(f"Scan error for {asset}: {e}")
        
    finally:
        db.close()


async def whale_alert_check():
    """Check for significant whale movements"""
    from app.db.session import SessionLocal
    from app.api.endpoints.alerts import check_and_trigger_alerts
    
    db = SessionLocal()
    try:
        # TODO: Integrate with whale tracking API
        # For now, this is a placeholder
        logger.info("Whale alert check running")
    finally:
        db.close()


def setup_scheduler():
    """Configure scheduled tasks"""
    # Hourly portfolio scan
    scheduler.add_task("hourly_scan", 3600, hourly_portfolio_scan)
    
    # Whale alerts every 5 minutes
    scheduler.add_task("whale_check", 300, whale_alert_check)
    
    logger.info("Scheduler tasks configured")


async def start_scheduler():
    """Start the scheduler (call from main.py)"""
    setup_scheduler()
    await scheduler.start()
