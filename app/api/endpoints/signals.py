"""
Signal Ingestion & Notification API
Receives signals from Lambda scanner and pushes to users
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
from app.db.session import get_db
from app.models.user import User
from app.models.signal import Signal
from app.core.deps import get_current_user
from app.core.logging import logger
import os

router = APIRouter()

# Service key for Lambda authentication
SERVICE_KEY = os.environ.get("ELUXRAJ_SERVICE_KEY", "eluxraj-lambda-signal-scanner-2026")


class SignalIngest(BaseModel):
    symbol: str
    timeframe: str
    signal_type: str
    confidence: int
    entry_price: float
    stop_loss: float
    target_1: float
    target_2: Optional[float] = None
    risk_reward: Optional[float] = None
    pattern: Optional[str] = None
    catalyst: Optional[str] = None
    urgency: Optional[str] = "medium"
    reasoning: Optional[str] = None


class NotifyRequest(BaseModel):
    signal_id: int
    symbol: str
    signal_type: str
    confidence: int
    tiers: List[str] = ["pro", "elite"]


def verify_service_key(x_service_key: str = Header(None)):
    """Verify the service key from Lambda"""
    if x_service_key != SERVICE_KEY:
        raise HTTPException(status_code=401, detail="Invalid service key")
    return True


@router.post("/ingest")
async def ingest_signal(
    signal: SignalIngest,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_service_key)
):
    """Ingest a signal from the Lambda scanner"""
    
    logger.info(f"Ingesting signal: {signal.symbol} {signal.signal_type} @ {signal.confidence}%")
    
    try:
        # Check for duplicate (same symbol, timeframe, type within last hour)
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        existing = db.query(Signal).filter(
            Signal.symbol == signal.symbol.upper(),
            Signal.timeframe == signal.timeframe,
            Signal.signal_type == signal.signal_type.lower(),
            Signal.created_at >= one_hour_ago
        ).first()
        
        if existing:
            logger.info(f"Duplicate signal ignored: {signal.symbol}")
            return {"status": "duplicate", "signal_id": existing.id}
        
        # Create new signal
        new_signal = Signal(
            symbol=signal.symbol.upper(),
            pair=f"{signal.symbol.upper()}/USD",
            asset_type="stock",
            timeframe=signal.timeframe,
            signal_type=signal.signal_type.lower(),
            oracle_score=signal.confidence,
        confidence=float(signal.confidence),
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            target_price=signal.target_1,
            target_2=signal.target_2,
            risk_reward=signal.risk_reward,
            pattern=signal.pattern,
            catalyst=signal.catalyst,
            urgency=signal.urgency,
            reasoning=signal.reasoning,
            status="active",
            source="lambda_scanner"
        )
        
        db.add(new_signal)
        db.commit()
        db.refresh(new_signal)
        
        logger.info(f"Signal created: ID {new_signal.id}")
        
        return {
            "status": "created",
            "signal_id": new_signal.id,
            "symbol": new_signal.symbol,
            "confidence": new_signal.oracle_score
        }
        
    except Exception as e:
        logger.error(f"Database error creating signal: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB Error: {str(e)}")


@router.post("/notify")
async def notify_users(
    request: NotifyRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_service_key)
):
    """Send push notifications for a signal to eligible users"""
    
    logger.info(f"Notifying users for signal {request.signal_id}: {request.symbol}")
    
    # Get users with push enabled in specified tiers
    users = db.query(User).filter(
        User.subscription_tier.in_(request.tiers),
        User.is_active == True
    ).all()
    
    logger.info(f"Found {len(users)} users to notify")
    
    sent_count = 0
    for user in users:
        try:
            # Send push notification
            emoji = "📈" if request.signal_type == "BUY" else "📉"
            title = f"{emoji} {request.symbol} Signal"
            body = f"{request.signal_type} signal at {request.confidence}% confidence"
            
            # iOS push (if device token exists)
            if hasattr(user, 'device_token') and user.device_token:
                try:
                    from app.services.apns_service import apns_service
                    await apns_service.send_trade_alert(
                        device_token=user.device_token,
                        asset=request.symbol,
                        action=request.signal_type,
                        price=0,
                        confidence=request.confidence
                    )
                    sent_count += 1
                except Exception as e:
                    logger.warning(f"APNs error for user {user.id}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to notify user {user.id}: {e}")
    
    return {
        "status": "sent",
        "users_notified": sent_count,
        "signal_id": request.signal_id
    }


@router.get("/active")
async def get_active_signals(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = 20
):
    """Get active signals for the user's tier"""
    
    signals = db.query(Signal).filter(
        Signal.status == "active"
    ).order_by(desc(Signal.created_at)).limit(limit).all()
    
    result = []
    for s in signals:
        signal_data = {
            "id": s.id,
            "symbol": s.symbol,
            "signal_type": s.signal_type,
            "confidence": s.oracle_score,
            "timeframe": s.timeframe,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "urgency": s.urgency
        }
        
        # Pro/Elite get full details
        if user.subscription_tier in ["pro", "elite"]:
            signal_data.update({
                "entry_price": s.entry_price,
                "stop_loss": s.stop_loss,
                "target_1": s.target_price,
                "target_2": s.target_2,
                "risk_reward": s.risk_reward,
                "pattern": s.pattern,
                "catalyst": s.catalyst,
                "reasoning": s.reasoning
            })
        
        result.append(signal_data)
    
    return {"signals": result, "count": len(result)}


@router.get("/history")
async def get_signal_history(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    limit: int = 50,
    status: Optional[str] = None
):
    """Get signal history with outcomes"""
    
    query = db.query(Signal)
    
    if status:
        query = query.filter(Signal.status == status)
    
    signals = query.order_by(desc(Signal.created_at)).limit(limit).all()
    
    return {
        "signals": [
            {
                "id": s.id,
                "symbol": s.symbol,
                "signal_type": s.signal_type,
                "confidence": s.oracle_score,
                "entry_price": s.entry_price,
                "target_price": s.target_price,
                "stop_loss": s.stop_loss,
                "status": s.status,
                "outcome_pnl": s.outcome_pnl_percent,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "outcome_at": s.outcome_at.isoformat() if s.outcome_at else None
            }
            for s in signals
        ],
        "count": len(signals)
    }


@router.get("/stats")
async def get_signal_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get signal performance statistics"""
    
    from sqlalchemy import func
    
    total = db.query(Signal).count()
    active = db.query(Signal).filter(Signal.status == "active").count()
    
    # Win rate
    closed = db.query(Signal).filter(Signal.status.in_(["hit_target", "hit_stop"])).all()
    wins = len([s for s in closed if s.status == "hit_target"])
    win_rate = (wins / len(closed) * 100) if closed else 0
    
    # Average P&L
    avg_pnl = db.query(func.avg(Signal.outcome_pnl_percent)).filter(
        Signal.outcome_pnl_percent.isnot(None)
    ).scalar() or 0
    
    # Signals today
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = db.query(Signal).filter(Signal.created_at >= today).count()
    
    return {
        "total_signals": total,
        "active_signals": active,
        "signals_today": today_count,
        "win_rate": round(win_rate, 1),
        "avg_pnl_percent": round(float(avg_pnl), 2),
        "closed_trades": len(closed)
    }
