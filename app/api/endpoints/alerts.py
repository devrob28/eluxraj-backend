from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.user import User
from app.models.signal import Signal
from app.services.email import email_service
from app.core.deps import get_current_user
from app.core.logging import logger

router = APIRouter()

@router.post("/test")
async def send_test_alert(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a test alert email to current user"""
    
    if not email_service.is_enabled():
        raise HTTPException(status_code=503, detail="Email service not configured")
    
    # Create a sample signal for testing
    test_signal = {
        "symbol": "BTC",
        "pair": "BTC/USDT",
        "signal_type": "buy",
        "oracle_score": 78,
        "entry_price": 89500.00,
        "target_price": 95000.00,
        "stop_loss": 86000.00,
        "risk_reward_ratio": 1.57,
        "timeframe": "48h",
        "reasoning_summary": "Strong bullish confluence detected. Volume surge +340% above 20-day average. RSI recovering from oversold. Whale accumulation: 2,400 BTC in last 4 hours. Market sentiment at extreme fear - contrarian opportunity."
    }
    
    # Send in background
    background_tasks.add_task(
        email_service.send_signal_alert,
        current_user.email,
        current_user.full_name,
        test_signal
    )
    
    return {
        "message": f"Test alert sent to {current_user.email}",
        "signal": test_signal
    }

@router.post("/send/{signal_id}")
async def send_alert_for_signal(
    signal_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send alert for a specific signal"""
    
    if not email_service.is_enabled():
        raise HTTPException(status_code=503, detail="Email service not configured")
    
    signal = db.query(Signal).filter(Signal.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    signal_data = {
        "symbol": signal.symbol,
        "pair": signal.pair,
        "signal_type": signal.signal_type,
        "oracle_score": signal.oracle_score,
        "entry_price": signal.entry_price,
        "target_price": signal.target_price,
        "stop_loss": signal.stop_loss,
        "risk_reward_ratio": signal.risk_reward_ratio,
        "timeframe": signal.timeframe,
        "reasoning_summary": signal.reasoning_summary
    }
    
    background_tasks.add_task(
        email_service.send_signal_alert,
        current_user.email,
        current_user.full_name,
        signal_data
    )
    
    return {"message": f"Alert sent to {current_user.email}", "signal_id": signal_id}

@router.get("/status")
async def get_alert_status():
    """Check email service status"""
    return {
        "email_enabled": email_service.is_enabled(),
        "from_email": email_service.from_email
    }
