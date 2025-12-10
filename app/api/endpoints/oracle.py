"""
ORACLE API Endpoints - v3.0 Institutional Grade
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app.services.oracle_v3 import oracle_v3
from app.api.deps import get_current_user, require_elite
from app.core.logging import logger

router = APIRouter()


@router.get("/{symbol}")
async def get_oracle_signal(
    symbol: str,
    user = Depends(require_elite)
):
    """
    Get ORACLE v3.0 signal for an asset
    
    Features institutional-grade quant models:
    - Time-Series Momentum (AQR style)
    - Statistical Arbitrage (Two Sigma style)
    - Risk Metrics (Goldman Sachs style)
    - Volume Analysis (Market Microstructure)
    
    Requires Elite subscription ($98/mo)
    """
    try:
        signal = await oracle_v3.generate_signal(symbol.upper())
        
        if not signal:
            raise HTTPException(
                status_code=404,
                detail=f"Unable to generate signal for {symbol}. Asset may not be supported."
            )
        
        return signal
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Oracle error for {symbol}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate ORACLE signal"
        )


@router.get("/{symbol}/quant")
async def get_quant_models(
    symbol: str,
    user = Depends(require_elite)
):
    """
    Get detailed quant model breakdown
    
    Returns individual model results:
    - TSMOM (Time-Series Momentum)
    - RSI with divergence
    - Bollinger Z-Score
    - Ornstein-Uhlenbeck mean reversion
    - VaR and risk metrics
    - Sharpe/Sortino ratios
    - Trend indicators
    - Volume analysis
    """
    try:
        analysis = await oracle_v3.analyze_asset(symbol.upper())
        
        if not analysis or not analysis.get("quant_results"):
            raise HTTPException(
                status_code=404,
                detail=f"Unable to run quant models for {symbol}"
            )
        
        return {
            "symbol": symbol.upper(),
            "quant_models": analysis["quant_results"],
            "price": analysis.get("price_data", {}).get("current_price"),
            "model_version": oracle_v3.MODEL_VERSION,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quant models error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to run quant models")


@router.get("/")
async def get_oracle_overview(
    user = Depends(require_elite)
):
    """
    Get ORACLE signals for all supported assets
    """
    try:
        signals = []
        for symbol in oracle_v3.SUPPORTED_ASSETS[:6]:  # Top 6 for performance
            try:
                signal = await oracle_v3.generate_signal(symbol)
                if signal:
                    signals.append({
                        "symbol": signal["symbol"],
                        "oracle_score": signal["oracle_score"],
                        "signal_type": signal["signal_type"],
                        "confidence": signal["confidence"],
                        "price": signal["price"],
                        "price_change_24h": signal["price_change_24h"],
                        "quant_signal": signal.get("quant_models", {}).get("signal", "HOLD"),
                    })
            except Exception as e:
                logger.warning(f"Failed to get signal for {symbol}: {e}")
        
        # Sort by score
        signals.sort(key=lambda x: x["oracle_score"], reverse=True)
        
        return {
            "signals": signals,
            "model_version": oracle_v3.MODEL_VERSION,
            "supported_assets": oracle_v3.SUPPORTED_ASSETS,
        }
        
    except Exception as e:
        logger.error(f"Oracle overview error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get ORACLE overview")


@router.get("/assets/supported")
async def get_supported_assets():
    """Get list of supported assets"""
    return {
        "assets": oracle_v3.SUPPORTED_ASSETS,
        "model_version": oracle_v3.MODEL_VERSION,
    }
