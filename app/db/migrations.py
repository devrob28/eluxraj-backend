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

        # Add device_token column for iOS push notifications
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS device_token VARCHAR(255)"))
            conn.commit()
            logger.info("✅ Migration: device_token column ready")
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

def add_push_subscription_column(engine):
    """Add push_subscription column to users table"""
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS push_subscription JSON"))
            conn.commit()
            logger.info("Added push_subscription column")
        except Exception as e:
            logger.warning(f"push_subscription column may already exist: {e}")

def add_playbook_tables(engine):
    """Add trade_playbooks table"""
    with engine.connect() as conn:
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS trade_playbooks (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    asset VARCHAR(50) NOT NULL,
                    asset_type VARCHAR(20) NOT NULL,
                    timeframe VARCHAR(10) NOT NULL,
                    market_bias VARCHAR(20) NOT NULL,
                    bias_strength FLOAT NOT NULL,
                    entry_zone_low FLOAT NOT NULL,
                    entry_zone_high FLOAT NOT NULL,
                    stop_loss FLOAT NOT NULL,
                    take_profit_1 FLOAT NOT NULL,
                    take_profit_2 FLOAT NOT NULL,
                    take_profit_3 FLOAT NOT NULL,
                    risk_reward_ratio FLOAT NOT NULL,
                    probability_score FLOAT NOT NULL,
                    confidence_score FLOAT NOT NULL,
                    bullish_scenarios JSON,
                    bearish_scenarios JSON,
                    invalidation_conditions JSON,
                    invalidation_price FLOAT,
                    pattern_detected VARCHAR(100),
                    market_structure VARCHAR(50),
                    reasoning TEXT,
                    status VARCHAR(20) DEFAULT 'active',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    expires_at TIMESTAMP WITH TIME ZONE
                )
            """))
            conn.commit()
            logger.info("Created trade_playbooks table")
        except Exception as e:
            logger.warning(f"trade_playbooks table may exist: {e}")


def add_api_usage_table(engine):
    """Add API usage tracking table"""
    with engine.connect() as conn:
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS api_usage (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    feature VARCHAR(50) NOT NULL,
                    date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    count INTEGER DEFAULT 1
                );
                
                CREATE INDEX IF NOT EXISTS idx_usage_user_feature_date 
                ON api_usage(user_id, feature, date);
            """))
            conn.commit()
            logger.info("Created api_usage table")
        except Exception as e:
            logger.warning(f"api_usage table may exist: {e}")


def add_chart_analyses_table(engine):
    """Add chart_analyses table for history"""
    with engine.connect() as conn:
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS chart_analyses (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    asset VARCHAR(50) NOT NULL,
                    timeframe VARCHAR(20) NOT NULL,
                    pattern_detected VARCHAR(100),
                    market_structure VARCHAR(50),
                    key_levels JSON,
                    trade_recommendation VARCHAR(20),
                    trade_setup JSON,
                    bullish_scenarios JSON,
                    bearish_scenarios JSON,
                    invalidation_conditions JSON,
                    confidence_score FLOAT DEFAULT 0,
                    reasoning TEXT,
                    status VARCHAR(20) DEFAULT 'active',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_chart_analyses_user 
                ON chart_analyses(user_id, created_at DESC);
            """))
            conn.commit()
            logger.info("Created chart_analyses table")
        except Exception as e:
            logger.warning(f"chart_analyses table may exist: {e}")
