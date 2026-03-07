"""
Referral System - 30% recurring commission for affiliates
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from typing import Optional
import secrets
import string

from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


def generate_referral_code(length=8):
    """Generate a unique referral code"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


@router.get("/my-code")
async def get_my_referral_code(
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get or create user's referral code"""
    if not user.referral_code:
        # Generate unique code
        while True:
            code = generate_referral_code()
            existing = db.query(User).filter(User.referral_code == code).first()
            if not existing:
                break
        
        user.referral_code = code
        db.commit()
    
    return {
        "referral_code": user.referral_code,
        "referral_link": f"https://eluxraj.ai/register.html?ref={user.referral_code}",
        "commission_rate": "30%",
        "commission_type": "recurring"
    }


@router.get("/stats")
async def get_referral_stats(
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get referral statistics"""
    
    # Count referred users
    referred_users = db.query(User).filter(User.referred_by == user.id).all()
    
    total_referrals = len(referred_users)
    active_referrals = sum(1 for u in referred_users if u.subscription_tier in ['pro', 'elite'])
    
    # Calculate earnings (30% of their subscription)
    monthly_earnings = 0
    for ref in referred_users:
        if ref.subscription_tier == 'pro':
            monthly_earnings += 49 * 0.30  # $14.70 per pro user
        elif ref.subscription_tier == 'elite':
            monthly_earnings += 99 * 0.30  # $29.70 per elite user
    
    return {
        "total_referrals": total_referrals,
        "active_paid_referrals": active_referrals,
        "monthly_earnings": round(monthly_earnings, 2),
        "lifetime_earnings": round(monthly_earnings * 12, 2),  # Simplified
        "pending_payout": round(monthly_earnings, 2),
        "referral_code": user.referral_code,
        "referral_link": f"https://eluxraj.ai/register.html?ref={user.referral_code}"
    }


@router.get("/leaderboard")
async def get_referral_leaderboard(
    db: Session = Depends(get_db)
):
    """Public leaderboard of top affiliates"""
    
    # Get top referrers
    top_referrers = db.query(
        User.id,
        User.email,
        func.count(User.id).label('referral_count')
    ).join(
        User, User.referred_by == User.id, isouter=True
    ).group_by(User.id).order_by(func.count(User.id).desc()).limit(10).all()
    
    leaderboard = []
    for i, (user_id, email, count) in enumerate(top_referrers):
        if count > 0:
            leaderboard.append({
                "rank": i + 1,
                "username": email.split('@')[0][:3] + "***",
                "referrals": count
            })
    
    return {"leaderboard": leaderboard}
