from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import datetime, timedelta
from app.db.session import get_db
from app.models.user import User
from app.models.signal import Signal
from app.schemas.signal import SignalResponse, SignalListResponse
from app.core.deps import get_current_user

router = APIRouter()

@router.get("/", response_model=SignalListResponse)
async def get_signals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    asset_type: Optional[str] = None,
    symbol: Optional[str] = None,
    min_score: int = Query(60, ge=0, le=100),
    status: Optional[str] = "active",
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """Get trading signals"""
    query = db.query(Signal)
    
    if asset_type:
        query = query.filter(Signal.asset_type == asset_type)
    if symbol:
        query = query.filter(Signal.symbol == symbol.upper())
    if status:
        query = query.filter(Signal.status == status)
    
    query = query.filter(Signal.oracle_score >= min_score)
    
    # Free tier restrictions
    if current_user.subscription_tier == "free":
        delay_cutoff = datetime.utcnow() - timedelta(hours=2)
        query = query.filter(Signal.created_at <= delay_cutoff)
        query = query.filter(Signal.symbol.in_(["BTC", "ETH", "SOL"]))
    
    total = query.count()
    offset = (page - 1) * per_page
    signals = query.order_by(desc(Signal.created_at)).offset(offset).limit(per_page).all()
    
    return SignalListResponse(
        signals=signals,
        total=total,
        page=page,
        per_page=per_page
    )

@router.get("/performance/summary")
async def get_performance_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(30, ge=7, le=365)
):
    """Get signal performance summary"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    completed = db.query(Signal).filter(
        Signal.created_at >= cutoff,
        Signal.status.in_(["hit_target", "hit_stop", "expired"])
    ).all()
    
    if not completed:
        return {
            "period_days": days,
            "total_signals": 0,
            "win_rate": 0,
            "avg_return": 0,
            "total_return": 0
        }
    
    wins = [s for s in completed if s.status == "hit_target"]
    total_pnl = sum(s.outcome_pnl_percent or 0 for s in completed)
    avg_pnl = total_pnl / len(completed)
    
    return {
        "period_days": days,
        "total_signals": len(completed),
        "wins": len(wins),
        "losses": len(completed) - len(wins),
        "win_rate": round(len(wins) / len(completed) * 100, 1),
        "avg_return": round(avg_pnl, 2),
        "total_return": round(total_pnl, 2)
    }
