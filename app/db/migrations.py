"""
Database migrations - runs on startup
"""
from sqlalchemy import text
from app.core.logging import logger


def run_migrations(engine):
    """Run pending migrations"""
    with engine.connect() as conn:
        # Add phone column to users if not exists
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20)"))
            conn.commit()
            logger.info("✅ Migration: phone column ready")
        except Exception as e:
            logger.warning(f"Migration note: {e}")

        # Add all columns to weekly_briefs
        try:
            conn.execute(text("ALTER TABLE weekly_briefs ADD COLUMN IF NOT EXISTS crypto_top_performers JSON"))
            conn.execute(text("ALTER TABLE weekly_briefs ADD COLUMN IF NOT EXISTS crypto_worst_performers JSON"))
            conn.execute(text("ALTER TABLE weekly_briefs ADD COLUMN IF NOT EXISTS stock_top_performers JSON"))
            conn.execute(text("ALTER TABLE weekly_briefs ADD COLUMN IF NOT EXISTS stock_worst_performers JSON"))
            conn.execute(text("ALTER TABLE weekly_briefs ADD COLUMN IF NOT EXISTS tier_required VARCHAR(20) DEFAULT 'pro'"))
            conn.execute(text("ALTER TABLE weekly_briefs ADD COLUMN IF NOT EXISTS key_events JSON"))
            conn.execute(text("ALTER TABLE weekly_briefs ADD COLUMN IF NOT EXISTS bull_case TEXT"))
            conn.execute(text("ALTER TABLE weekly_briefs ADD COLUMN IF NOT EXISTS bear_case TEXT"))
            conn.execute(text("ALTER TABLE weekly_briefs ADD COLUMN IF NOT EXISTS base_case TEXT"))
            conn.execute(text("ALTER TABLE weekly_briefs ADD COLUMN IF NOT EXISTS market_overview TEXT"))
            conn.commit()
            logger.info("✅ Migration: weekly_briefs columns ready")
        except Exception as e:
            logger.warning(f"Migration note: {e}")
