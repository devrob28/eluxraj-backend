from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
from datetime import datetime, timedelta
from app.db.session import get_db
from app.models.user import User
from app.models.signal import Signal
from app.core.deps import get_current_user
from app.core.logging import logger

router = APIRouter()

# Simple admin check - in production, use a proper admin role
ADMIN_EMAILS = ["robmdata@gmail.com", "admin@eluxraj.ai"]

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# ============== DASHBOARD STATS ==============

@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get overall dashboard statistics"""
    
    # User stats
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    
    users_by_tier = db.query(
        User.subscription_tier,
        func.count(User.id)
    ).group_by(User.subscription_tier).all()
    
    tier_counts = {tier: count for tier, count in users_by_tier}
    
    # New users (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    new_users_week = db.query(User).filter(User.created_at >= week_ago).count()
    
    # Signal stats
    total_signals = db.query(Signal).count()
    active_signals = db.query(Signal).filter(Signal.status == "active").count()
    
    signals_by_type = db.query(
        Signal.signal_type,
        func.count(Signal.id)
    ).group_by(Signal.signal_type).all()
    
    type_counts = {stype: count for stype, count in signals_by_type}
    
    # Signals today
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    signals_today = db.query(Signal).filter(Signal.created_at >= today).count()
    
    # Average oracle score
    avg_score = db.query(func.avg(Signal.oracle_score)).scalar() or 0
    
    # Revenue estimate
    pro_users = tier_counts.get("pro", 0)
    elite_users = tier_counts.get("elite", 0)
    mrr = (pro_users * 98) + (elite_users * 197)
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "new_this_week": new_users_week,
            "by_tier": {
                "free": tier_counts.get("free", 0),
                "pro": tier_counts.get("pro", 0),
                "elite": tier_counts.get("elite", 0),
            }
        },
        "signals": {
            "total": total_signals,
            "active": active_signals,
            "today": signals_today,
            "avg_oracle_score": round(avg_score, 1),
            "by_type": {
                "buy": type_counts.get("buy", 0),
                "sell": type_counts.get("sell", 0),
                "hold": type_counts.get("hold", 0),
            }
        },
        "revenue": {
            "mrr": mrr,
            "arr": mrr * 12,
        },
        "generated_at": datetime.utcnow().isoformat()
    }

# ============== USER MANAGEMENT ==============

@router.get("/users")
async def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    tier: Optional[str] = None,
    search: Optional[str] = None
):
    """List all users with pagination"""
    
    query = db.query(User)
    
    if tier:
        query = query.filter(User.subscription_tier == tier)
    
    if search:
        query = query.filter(
            (User.email.ilike(f"%{search}%")) |
            (User.full_name.ilike(f"%{search}%"))
        )
    
    total = query.count()
    offset = (page - 1) * per_page
    
    users = query.order_by(desc(User.created_at)).offset(offset).limit(per_page).all()
    
    return {
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "subscription_tier": u.subscription_tier,
                "is_active": u.is_active,
                "is_verified": u.is_verified,
                "email_alerts": u.email_alerts,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "last_login": u.last_login.isoformat() if u.last_login else None,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page
    }

@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Get user details"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "subscription_tier": user.subscription_tier,
        "stripe_customer_id": user.stripe_customer_id,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "email_alerts": user.email_alerts,
        "push_alerts": user.push_alerts,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }

@router.patch("/users/{user_id}/tier")
async def update_user_tier(
    user_id: int,
    tier: str,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Upgrade/downgrade user subscription tier"""
    
    if tier not in ["free", "pro", "elite"]:
        raise HTTPException(status_code=400, detail="Invalid tier")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    old_tier = user.subscription_tier
    user.subscription_tier = tier
    db.commit()
    
    logger.info(f"Admin updated user {user.email} from {old_tier} to {tier}")
    
    return {"message": f"User upgraded to {tier}", "user_id": user_id, "old_tier": old_tier, "new_tier": tier}

@router.patch("/users/{user_id}/status")
async def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Activate/deactivate user"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = not user.is_active
    db.commit()
    
    status = "activated" if user.is_active else "deactivated"
    logger.info(f"Admin {status} user {user.email}")
    
    return {"message": f"User {status}", "user_id": user_id, "is_active": user.is_active}

# ============== SIGNAL MANAGEMENT ==============

@router.get("/signals")
async def list_signals(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    symbol: Optional[str] = None
):
    """List all signals with pagination"""
    
    query = db.query(Signal)
    
    if status:
        query = query.filter(Signal.status == status)
    
    if symbol:
        query = query.filter(Signal.symbol == symbol.upper())
    
    total = query.count()
    offset = (page - 1) * per_page
    
    signals = query.order_by(desc(Signal.created_at)).offset(offset).limit(per_page).all()
    
    return {
        "signals": [
            {
                "id": s.id,
                "symbol": s.symbol,
                "pair": s.pair,
                "signal_type": s.signal_type,
                "oracle_score": s.oracle_score,
                "entry_price": s.entry_price,
                "target_price": s.target_price,
                "stop_loss": s.stop_loss,
                "status": s.status,
                "outcome_pnl_percent": s.outcome_pnl_percent,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "expires_at": s.expires_at.isoformat() if s.expires_at else None,
            }
            for s in signals
        ],
        "total": total,
        "page": page,
        "per_page": per_page
    }

@router.patch("/signals/{signal_id}/status")
async def update_signal_status(
    signal_id: int,
    status: str,
    outcome_price: Optional[float] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Update signal status (hit_target, hit_stop, expired, cancelled)"""
    
    valid_statuses = ["active", "hit_target", "hit_stop", "expired", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    signal = db.query(Signal).filter(Signal.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    signal.status = status
    signal.outcome_at = datetime.utcnow()
    
    if outcome_price:
        signal.outcome_price = outcome_price
        # Calculate P&L
        if signal.signal_type == "buy":
            signal.outcome_pnl_percent = ((outcome_price - signal.entry_price) / signal.entry_price) * 100
        else:
            signal.outcome_pnl_percent = ((signal.entry_price - outcome_price) / signal.entry_price) * 100
    
    db.commit()
    
    logger.info(f"Admin updated signal {signal_id} to {status}")
    
    return {"message": f"Signal updated to {status}", "signal_id": signal_id}

@router.delete("/signals/{signal_id}")
async def delete_signal(
    signal_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Delete a signal"""
    
    signal = db.query(Signal).filter(Signal.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    db.delete(signal)
    db.commit()
    
    logger.info(f"Admin deleted signal {signal_id}")
    
    return {"message": "Signal deleted", "signal_id": signal_id}

# ============== SYSTEM CONTROLS ==============

@router.post("/system/scan")
async def trigger_market_scan(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Manually trigger a market scan"""
    from app.services.scheduler import scheduled_market_scan
    
    result = await scheduled_market_scan()
    return {"message": "Scan completed", "result": result}

@router.post("/system/cleanup")
async def trigger_cleanup(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Manually trigger expired signal cleanup"""
    from app.services.scheduler import cleanup_expired_signals
    
    await cleanup_expired_signals()
    return {"message": "Cleanup completed"}

@router.get("/system/health")
async def get_system_health(
    admin: User = Depends(require_admin)
):
    """Get detailed system health"""
    from app.services.scheduler import get_scheduled_jobs
    from app.services.email import email_service
    
    return {
        "api": "healthy",
        "scheduler": {
            "status": "running",
            "jobs": get_scheduled_jobs()
        },
        "email": {
            "enabled": email_service.is_enabled(),
            "from": email_service.from_email
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/system/broadcast")
async def broadcast_email(
    subject: str,
    message: str,
    tier: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Send broadcast email to users"""
    from app.services.email import email_service
    
    if not email_service.is_enabled():
        raise HTTPException(status_code=503, detail="Email service not configured")
    
    query = db.query(User).filter(User.is_active == True, User.email_alerts == True)
    
    if tier:
        query = query.filter(User.subscription_tier == tier)
    
    users = query.all()
    sent = 0
    
    for user in users:
        try:
            await email_service.send_email(user.email, subject, message)
            sent += 1
        except:
            pass
    
    return {"message": f"Broadcast sent to {sent} users", "total_recipients": len(users)}
