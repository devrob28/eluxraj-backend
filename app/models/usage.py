"""API Usage Tracking Model"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.db.base import Base

class APIUsage(Base):
    """Track API usage per user per feature per day"""
    __tablename__ = "api_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    feature = Column(String(50), nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    count = Column(Integer, default=1, nullable=False)
    
    __table_args__ = (
        Index('idx_usage_user_feature_date', 'user_id', 'feature', 'date'),
    )


# ═══════════════════════════════════════════════════════════════
# RATE LIMITS BY TIER
# ═══════════════════════════════════════════════════════════════
# Pricing: Pro = $53/mo, Elite = $98/mo
# 
# LITE ($35/mo):     Basic dashboard only, no AI features
# PRO ($53/mo):    Limited AI access, good for casual traders
# ELITE ($98/mo): Unlimited everything, institutional-grade
# ═══════════════════════════════════════════════════════════════

RATE_LIMITS = {
    # AI Trade Playbooks - Complete trade setups with entry/exit/stops
    "playbook": {
        "lite": 0,       # No access
        "pro": 5,        # 5 per day
        "elite": 9999,   # Unlimited
        "admin": 9999,
    },
    
    # Chart AI Analysis - Upload chart images for AI analysis
    "chart_analysis": {
        "lite": 0,       # No access
        "pro": 10,       # 10 per day
        "elite": 9999,   # Unlimited
        "admin": 9999,
    },
    
    # Whale Intel - Track smart money movements
    "whale_intel": {
        "lite": 3,       # 3 views per day (teaser)
        "pro": 50,       # 50 per day
        "elite": 9999,   # Unlimited
        "admin": 9999,
    },
    
    
    # Weekly AI Brief - Comprehensive market analysis
    "weekly_brief": {
        "lite": 0,       # No access
        "pro": 1,        # 1 per week (it's weekly anyway)
        "elite": 9999,   # Unlimited
        "admin": 9999,
    },
    
    # Custom Alerts - Price/whale/insider alerts
    "alerts": {
        "lite": 1,       # 1 alert
        "pro": 10,       # 10 alerts
        "elite": 100,    # 100 alerts
        "admin": 9999,
    },
    
}


# Feature descriptions for upgrade prompts
FEATURE_DESCRIPTIONS = {
    "playbook": "AI Trade Playbooks with complete entry/exit strategies",
    "chart_analysis": "AI Chart Pattern Analysis with Fibonacci levels",
    "whale_intel": "Real-time Whale & Insider Trading Intelligence",
    "weekly_brief": "Weekly AI Market Analysis Brief",
    "alerts": "Custom Price & Whale Alerts",
}


# Tier pricing for upgrade prompts
TIER_PRICING = {
    "lite": "$35/mo",
    "pro": "$53/mo",
    "elite": "$98/mo",
}
