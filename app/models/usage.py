"""API Usage Tracking Model"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.db.session import Base

class APIUsage(Base):
    """Track API usage per user per feature per day"""
    __tablename__ = "api_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    feature = Column(String(50), nullable=False)  # 'playbook', 'chart_analysis', etc.
    date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    count = Column(Integer, default=1, nullable=False)
    
    # Composite index for efficient lookups
    __table_args__ = (
        Index('idx_usage_user_feature_date', 'user_id', 'feature', 'date'),
    )


# Rate limits by tier and feature
RATE_LIMITS = {
    "playbook": {
        "lite": 0,      # No access
        "pro": 5,       # 5 per day
        "elite": 999,   # Unlimited (high number)
        "admin": 999,   # Unlimited
    },
    "chart_analysis": {
        "lite": 0,      # No access
        "pro": 10,      # 10 per day
        "elite": 999,   # Unlimited
        "admin": 999,   # Unlimited
    }
}
