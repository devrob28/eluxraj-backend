"""API Usage Endpoint"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.deps import get_current_user
from app.services.rate_limiter import rate_limiter
from app.models.usage import RATE_LIMITS

router = APIRouter()


@router.get("/")
async def get_usage(
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current API usage and limits for the authenticated user"""
    stats = rate_limiter.get_usage(db, user.id, user.subscription_tier)
    
    return {
        "user_id": user.id,
        "tier": user.subscription_tier,
        "usage": stats,
        "limits": {
            feature: RATE_LIMITS[feature].get(user.subscription_tier, 0)
            for feature in RATE_LIMITS
        },
        "resets_at": "00:00 UTC daily"
    }
