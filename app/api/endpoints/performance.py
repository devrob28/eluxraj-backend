"""
Performance Tracking API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.db.session import get_db
from app.core.deps import get_current_user
from app.services.performance_service import performance_service

router = APIRouter()


class TradeRequest(BaseModel):
    symbol: str
    side: str  # buy, sell
    quantity: float
    price: float
    asset_type: str = "crypto"
    source: str = "manual"


class SignalRequest(BaseModel):
    symbol: str
    signal_type: str  # buy, sell
    entry_price: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    confidence: float = 70.0
    reasoning: Optional[str] = None
    asset_type: str = "crypto"


class CloseSignalRequest(BaseModel):
    exit_price: float


@router.get("/stats")
async def get_performance_stats(
    days: int = 30,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user performance statistics"""
    comparison = performance_service.compare_performance(db, user.id, days)
    return {"ok": True, **comparison}


@router.get("/trades")
async def get_user_trades(
    limit: int = 50,
    symbol: Optional[str] = None,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's trade history"""
    trades = performance_service.get_user_trades(db, user.id, limit, symbol)
    return {"ok": True, "count": len(trades), "trades": trades}


@router.post("/trades")
async def add_trade(
    req: TradeRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record a trade"""
    trade = performance_service.add_user_trade(
        db=db,
        user_id=user.id,
        symbol=req.symbol,
        side=req.side,
        quantity=req.quantity,
        price=req.price,
        asset_type=req.asset_type,
        source=req.source
    )
    return {"ok": True, "message": "Trade recorded", "trade_id": trade.id}


@router.get("/signals")
async def get_signals(
    limit: int = 50,
    symbol: Optional[str] = None,
    outcome: Optional[str] = None,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ELUXRAJ signal history"""
    signals = performance_service.get_signal_history(db, limit, symbol, outcome)
    return {"ok": True, "count": len(signals), "signals": signals}


@router.post("/signals")
async def add_signal(
    req: SignalRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record a new signal (admin/elite only)"""
    if user.subscription_tier not in ["admin", "elite"] and not getattr(user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Elite or admin required")
    
    signal = performance_service.add_signal(
        db=db,
        symbol=req.symbol,
        signal_type=req.signal_type,
        entry_price=req.entry_price,
        target_price=req.target_price,
        stop_loss=req.stop_loss,
        confidence=req.confidence,
        reasoning=req.reasoning,
        asset_type=req.asset_type
    )
    return {"ok": True, "message": "Signal recorded", "signal_id": signal.id}


@router.put("/signals/{signal_id}/close")
async def close_signal(
    signal_id: int,
    req: CloseSignalRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Close a signal with exit price (admin/elite only)"""
    if user.subscription_tier not in ["admin", "elite"] and not getattr(user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Elite or admin required")
    
    signal = performance_service.close_signal(db, signal_id, req.exit_price)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    return {
        "ok": True,
        "message": "Signal closed",
        "outcome": signal.outcome,
        "pnl_percent": signal.pnl_percent
    }


@router.get("/signal-stats")
async def get_signal_stats(
    days: int = 30,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ELUXRAJ signal performance stats"""
    stats = performance_service.get_signal_stats(db, days)
    return {"ok": True, **stats}


@router.get("/compare")
async def compare_performance(
    days: int = 30,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Compare user vs ELUXRAJ performance"""
    comparison = performance_service.compare_performance(db, user.id, days)
    return {"ok": True, **comparison}
