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
            conn.execute(text("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20)
            """))
            conn.commit()
            logger.info("✅ Migration: phone column ready")
        except Exception as e:
            logger.warning(f"Migration note: {e}")
