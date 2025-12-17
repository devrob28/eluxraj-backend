"""
Weekly Brief API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user
from app.services.weekly_brief import weekly_brief_service

router = APIRouter()

@router.get("")
async def get_weekly_brief(user=Depends(get_current_user), db: Session=Depends(get_db)):
    """Get latest weekly brief"""
    brief = weekly_brief_service.get_latest_brief(db, user.subscription_tier)
    if not brief:
        return {"ok": False, "message": "No weekly brief available yet"}
    return {"ok": True, "brief": brief}

@router.get("/archive")
async def get_brief_archive(limit: int=10, user=Depends(get_current_user), db: Session=Depends(get_db)):
    """Get archive of past briefs"""
    briefs = weekly_brief_service.get_all_briefs(db, limit)
    return {"ok": True, "count": len(briefs), "briefs": briefs}

@router.post("/generate")
async def generate_brief(user=Depends(get_current_user), db: Session=Depends(get_db)):
    """Manually generate a new brief (admin only)"""
    if user.subscription_tier != "admin" and not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    
    brief = await weekly_brief_service.generate_weekly_brief(db)
    return {"ok": True, "message": "Brief generated", "title": brief.title}
