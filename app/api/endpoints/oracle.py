from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.session import get_db
from app.models.user import User
from app.models.signal import Signal
from app.services.oracle import oracle
from app.services.scanner import scanner
from app.core.deps import get_current_user
from app.core.logging import logger

router = APIRouter()

@router.get("/analyze/{symbol}")
async def analyze_asset(
    symbol: str,
    current_user: User = Depends(get_current_user)
):
    """Analyze a single asset and return detailed factors"""
    analysis = await oracle.analyze_asset(symbol.upper())
    
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Could not analyze {symbol}")
    
    return {
        "symbol": analysis["symbol"],
        "factors": analysis["factors"],
        "price": analysis["price_data"].get("current_price"),
        "price_change_24h": analysis["price_data"].get("price_change_24h"),
        "market_sentiment": analysis.get("fng_data"),
        "timestamp": analysis["timestamp"],
    }

@router.get("/signal/{symbol}")
async def get_signal_for_asset(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a trading signal for a specific asset"""
    signal_data = await oracle.generate_signal(symbol.upper())
    
    if not signal_data:
        raise HTTPException(status_code=404, detail=f"Could not generate signal for {symbol}")
    
    # Free users get limited data
    if current_user.subscription_tier == "free":
        if symbol.upper() not in ["BTC", "ETH", "SOL"]:
            raise HTTPException(
                status_code=403,
                detail="Upgrade to Pro for all assets. Free tier includes BTC, ETH, SOL only."
            )
        signal_data["reasoning_factors"] = {}
        signal_data["input_snapshot"] = {}
    
    return signal_data

@router.post("/generate")
async def generate_and_save_signal(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a signal and save it to the database"""
    if current_user.subscription_tier == "free":
        raise HTTPException(status_code=403, detail="Signal generation requires Pro subscription")
    
    signal_data = await oracle.generate_signal(symbol.upper())
    
    if not signal_data:
        raise HTTPException(status_code=404, detail=f"Could not generate signal for {symbol}")
    
    # Create signal in database
    signal = Signal(
        asset_type=signal_data["asset_type"],
        symbol=signal_data["symbol"],
        pair=signal_data["pair"],
        signal_type=signal_data["signal_type"],
        oracle_score=signal_data["oracle_score"],
        confidence=signal_data["confidence"],
        entry_price=signal_data["entry_price"],
        target_price=signal_data["target_price"],
        stop_loss=signal_data["stop_loss"],
        risk_reward_ratio=signal_data["risk_reward_ratio"],
        reasoning_summary=signal_data["reasoning_summary"],
        reasoning_factors=signal_data["reasoning_factors"],
        model_version=signal_data["model_version"],
        input_snapshot=signal_data["input_snapshot"],
        data_sources=signal_data["data_sources"],
        timeframe=signal_data["timeframe"],
        expires_at=datetime.fromisoformat(signal_data["expires_at"]),
        status="active",
    )
    
    db.add(signal)
    db.commit()
    db.refresh(signal)
    
    logger.info(f"Signal saved: {signal.symbol} - {signal.signal_type} - Score: {signal.oracle_score}")
    
    return {
        "saved": True,
        "signal_id": signal.id,
        "signal": signal_data
    }

@router.post("/scan-all")
async def scan_all_and_save(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Scan ALL assets and save actionable signals to database"""
    if current_user.subscription_tier != "elite":
        raise HTTPException(status_code=403, detail="Market scanning requires Elite subscription")
    
    result = await scanner.scan_and_save(db)
    return result

@router.get("/supported-assets")
async def get_supported_assets():
    """Get list of supported assets"""
    return {
        "assets": oracle.SUPPORTED_ASSETS,
        "total": len(oracle.SUPPORTED_ASSETS),
    }

@router.get("/health")
async def oracle_health():
    """Check Oracle engine health"""
    from app.services.data_providers import fear_greed
    
    btc_data = await oracle.analyze_asset("BTC")
    coingecko_status = "healthy" if btc_data else "error"
    
    fng = await fear_greed.get_current()
    fng_status = "healthy" if fng else "error"
    
    return {
        "oracle_version": oracle.MODEL_VERSION,
        "status": "healthy" if coingecko_status == "healthy" else "degraded",
        "providers": {
            "coingecko": coingecko_status,
            "fear_greed": fng_status,
        },
        "supported_assets": len(oracle.SUPPORTED_ASSETS),
    }
