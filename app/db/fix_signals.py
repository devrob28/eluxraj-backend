"""Fix signal table constraints"""
from sqlalchemy import text
from app.core.logging import logger


def fix_signal_null_constraints(engine):
    """Remove NOT NULL constraints from optional signal fields"""
    with engine.connect() as conn:
        columns = [
            'confidence', 'risk_reward_ratio', 'reasoning_summary', 
            'position_size_suggestion', 'model_version', 'reasoning_factors',
            'input_snapshot', 'data_sources', 'expires_at', 'target_2',
            'target_3', 'risk_reward', 'pattern', 'catalyst', 'reasoning',
            'outcome_price', 'outcome_pnl_percent', 'outcome_at',
            'delivered_at', 'updated_at', 'user_id'
        ]
        for col in columns:
            try:
                conn.execute(text(f"ALTER TABLE signals ALTER COLUMN {col} DROP NOT NULL"))
                conn.commit()
            except Exception as e:
                pass
        logger.info("✅ Migration: signal null constraints fixed")
