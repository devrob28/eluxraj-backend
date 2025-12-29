"""Rate Limiting Service - Pro vs Elite Tier Enforcement"""
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

from app.models.usage import APIUsage, RATE_LIMITS, FEATURE_DESCRIPTIONS, TIER_PRICING
from app.core.logging import logger


class RateLimiter:
    """Service to check and track API usage limits by tier"""
    
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
        tier = tier.lower() if tier else "lite"
        
        # Get limit for this tier/feature
        feature_limits = RATE_LIMITS.get(feature, {})
        limit = feature_limits.get(tier, 0)
        
        # No access at all
        if limit == 0:
            feature_name = FEATURE_DESCRIPTIONS.get(feature, feature.replace('_', ' ').title())
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "upgrade_required",
                    "message": f"Your {tier.upper()} plan doesn't include {feature_name}.",
                    "feature": feature,
                    "current_tier": tier,
                    "required_tier": "pro",
                    "upgrade_url": "/settings.html#subscription",
                    "cta": f"Upgrade to Pro ({TIER_PRICING['pro']}) to unlock this feature"
                }
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
        
        # Check limit (skip for unlimited tiers)
        is_unlimited = limit >= 9999
        if not is_unlimited and usage_count >= limit:
            feature_name = FEATURE_DESCRIPTIONS.get(feature, feature.replace('_', ' ').title())
            reset_time = today_end.strftime("%H:%M UTC")
            
            # Suggest upgrade path
            if tier == "lite":
                upgrade_tier = "pro"
                upgrade_msg = f"Upgrade to Pro ({TIER_PRICING['pro']}) for {RATE_LIMITS[feature].get('pro', 'more')} daily uses"
            elif tier == "pro":
                upgrade_tier = "elite"
                upgrade_msg = f"Upgrade to Elite ({TIER_PRICING['elite']}) for unlimited access"
            else:
                upgrade_tier = None
                upgrade_msg = "Contact support for higher limits"
            
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": f"Daily limit reached for {feature_name}",
                    "feature": feature,
                    "current_tier": tier,
                    "used": usage_count,
                    "limit": limit,
                    "resets_at": reset_time,
                    "upgrade_tier": upgrade_tier,
                    "upgrade_url": "/settings.html#subscription",
                    "cta": upgrade_msg
                }
            )
        
        # Record this usage
        usage = APIUsage(
            user_id=user_id,
            feature=feature,
            date=datetime.now(timezone.utc)
        )
        db.add(usage)
        db.commit()
        
        new_count = usage_count + 1
        remaining = "unlimited" if is_unlimited else max(0, limit - new_count)
        
        logger.info(f"API usage: user={user_id} tier={tier} feature={feature} count={new_count}/{limit}")
        
        return {
            "used": new_count,
            "limit": "unlimited" if is_unlimited else limit,
            "remaining": remaining,
            "tier": tier
        }
    
    @staticmethod
    def get_usage(db: Session, user_id: int, tier: str) -> dict:
        """Get current usage stats for all features"""
        tier = tier.lower() if tier else "lite"
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        stats = {}
        for feature in RATE_LIMITS.keys():
            limit = RATE_LIMITS[feature].get(tier, 0)
            is_unlimited = limit >= 9999
            
            count = db.query(func.count(APIUsage.id)).filter(
                APIUsage.user_id == user_id,
                APIUsage.feature == feature,
                APIUsage.date >= today_start,
                APIUsage.date < today_end
            ).scalar() or 0
            
            stats[feature] = {
                "used": count,
                "limit": "unlimited" if is_unlimited else limit,
                "remaining": "unlimited" if is_unlimited else max(0, limit - count),
                "has_access": limit > 0,
                "description": FEATURE_DESCRIPTIONS.get(feature, "")
            }
        
        return stats
    
    @staticmethod
    def check_access(tier: str, feature: str) -> bool:
        """Quick check if tier has access to feature (no DB call)"""
        tier = tier.lower() if tier else "lite"
        limit = RATE_LIMITS.get(feature, {}).get(tier, 0)
        return limit > 0


rate_limiter = RateLimiter()
