"""Rate Limiting Service"""
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

from app.models.usage import APIUsage, RATE_LIMITS
from app.core.logging import logger


class RateLimiter:
    """Service to check and track API usage limits"""
    
    @staticmethod
    def check_and_increment(
        db: Session,
        user_id: int,
        tier: str,
        feature: str
    ) -> dict:
        """
        Check if user can use feature and increment counter.
        Returns usage info dict.
        Raises HTTPException if limit exceeded.
        """
        # Get limit for this tier/feature
        feature_limits = RATE_LIMITS.get(feature, {})
        limit = feature_limits.get(tier, 0)
        
        if limit == 0:
            raise HTTPException(
                status_code=403,
                detail=f"Your subscription tier ({tier}) does not include access to {feature.replace('_', ' ')}. Please upgrade."
            )
        
        # Get today's start (UTC)
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # Count today's usage
        usage_count = db.query(func.count(APIUsage.id)).filter(
            APIUsage.user_id == user_id,
            APIUsage.feature == feature,
            APIUsage.date >= today_start,
            APIUsage.date < today_end
        ).scalar() or 0
        
        # Check limit (skip for elite/admin with high limits)
        if limit < 100 and usage_count >= limit:
            reset_time = today_end.strftime("%H:%M UTC")
            raise HTTPException(
                status_code=429,
                detail=f"Daily limit reached ({usage_count}/{limit} for {tier.title()}). Upgrade to Elite for unlimited access. Resets at midnight UTC."
            )
        
        # Record this usage
        usage = APIUsage(
            user_id=user_id,
            feature=feature,
            date=datetime.now(timezone.utc)
        )
        db.add(usage)
        db.commit()
        
        remaining = max(0, limit - usage_count - 1) if limit < 100 else "unlimited"
        
        logger.info(f"API usage: user={user_id} feature={feature} count={usage_count + 1}/{limit}")
        
        return {
            "used": usage_count + 1,
            "limit": limit if limit < 100 else "unlimited",
            "remaining": remaining
        }
    
    @staticmethod
    def get_usage(db: Session, user_id: int, tier: str) -> dict:
        """Get current usage stats for a user"""
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        stats = {}
        for feature in RATE_LIMITS.keys():
            limit = RATE_LIMITS[feature].get(tier, 0)
            count = db.query(func.count(APIUsage.id)).filter(
                APIUsage.user_id == user_id,
                APIUsage.feature == feature,
                APIUsage.date >= today_start,
                APIUsage.date < today_end
            ).scalar() or 0
            
            stats[feature] = {
                "used": count,
                "limit": limit if limit < 100 else "unlimited",
                "remaining": max(0, limit - count) if limit < 100 else "unlimited"
            }
        
        return stats


rate_limiter = RateLimiter()
