"""
ORACLE API Endpoints - v3.0 Institutional Grade
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app.api.deps import get_current_user, require_elite
from app.core.logging import logger

router = APIRouter()

# Try to import v3, fallback to v2
try:
    from app.services.oracle_v3 import oracle_v3 as oracle_engine
    ORACLE_VERSION = "v3.0"
except ImportError:
    from app.services.oracle import oracle as oracle_engine
    ORACLE_VERSION = "v2.0"


@router.get("/score/{symbol}")
async def get_oracle_score(
    symbol: str,
    user = Depends(require_elite)
):
    """
    Get full ORACLE v3.0 analysis for an asset
    
    Features institutional-grade quant models:
    - Time-Series Momentum (AQR style)
    - Statistical Arbitrage (Two Sigma style)
    - Risk Metrics (Goldman Sachs style)
    - Volume Analysis (Market Microstructure)
    
    Requires Elite subscription
    """
    try:
        signal = await oracle_engine.generate_signal(symbol.upper())
        
        if not signal:
            raise HTTPException(
                status_code=404,
                detail=f"Unable to generate signal for {symbol}"
            )
        
        return {
            "ok": True,
            "data": signal,
            "tier": user.subscription_tier,
            "model_version": signal.get("model_version", ORACLE_VERSION)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Oracle error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate ORACLE signal")


@router.get("/{symbol}")
async def get_oracle_signal(
    symbol: str,
    user = Depends(require_elite)
):
    """
    Get ORACLE v3.0 signal for an asset (alternate endpoint)
    """
    return await get_oracle_score(symbol, user)


@router.get("/{symbol}/quant")
async def get_quant_models(
    symbol: str,
    user = Depends(require_elite)
):
    """
    Get detailed quant model breakdown
    """
    try:
        if hasattr(oracle_engine, 'analyze_asset'):
            analysis = await oracle_engine.analyze_asset(symbol.upper())
        else:
            raise HTTPException(status_code=501, detail="Quant models not available in this version")
        
        if not analysis or not analysis.get("quant_results"):
            raise HTTPException(status_code=404, detail=f"Unable to run quant models for {symbol}")
        
        return {
            "symbol": symbol.upper(),
            "quant_models": analysis["quant_results"],
            "price": analysis.get("price_data", {}).get("current_price"),
            "model_version": getattr(oracle_engine, 'MODEL_VERSION', ORACLE_VERSION),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quant models error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to run quant models")


@router.get("/demo/{symbol}")
async def get_oracle_demo(symbol: str):
    """Get demo ORACLE data for non-Elite users"""
    try:
        signal = await oracle_engine.generate_signal(symbol.upper())
        
        if not signal:
            return {"ok": False, "message": "Unable to generate demo signal"}
        
        # Return limited data for demo
        return {
            "ok": True,
            "demo": True,
            "data": {
                "symbol": signal.get("symbol"),
                "oracle_score": signal.get("oracle_score"),
                "signal_type": signal.get("signal_type"),
                "confidence": signal.get("confidence"),
                "price": signal.get("price") or signal.get("entry_price"),
                "message": "Upgrade to Elite for full analysis with institutional quant models"
            }
        }
    except Exception as e:
        logger.error(f"Demo oracle error: {e}")
        return {"ok": False, "message": "Demo unavailable"}


@router.get("/scan")
async def scan_all_assets():
    """Scan all supported assets"""
    try:
        if hasattr(oracle_engine, 'scan_all_assets'):
            signals = await oracle_engine.scan_all_assets()
        else:
            signals = []
            for symbol in getattr(oracle_engine, 'SUPPORTED_ASSETS', ['BTC', 'ETH', 'SOL'])[:6]:
                try:
                    signal = await oracle_engine.generate_signal(symbol)
                    if signal:
                        signals.append({
                            "symbol": signal["symbol"],
                            "oracle_score": signal["oracle_score"],
                            "signal_type": signal["signal_type"],
                        })
                except:
                    pass
        
        return {"ok": True, "signals": signals}
    except Exception as e:
        logger.error(f"Scan error: {e}")
        return {"ok": False, "signals": []}


@router.get("/whale-alerts/{symbol}")
async def get_whale_alerts(symbol: str):
    """Get whale alerts for an asset"""
    try:
        if hasattr(oracle_engine, 'get_whale_alerts'):
            alerts = await oracle_engine.get_whale_alerts(symbol.upper())
            return {"ok": True, "alerts": alerts}
        return {"ok": True, "alerts": []}
    except Exception as e:
        logger.error(f"Whale alerts error: {e}")
        return {"ok": False, "alerts": []}


@router.get("/liquidation-map/{symbol}")
async def get_liquidation_map(symbol: str):
    """Get liquidation heatmap"""
    try:
        if hasattr(oracle_engine, 'get_liquidation_map'):
            data = await oracle_engine.get_liquidation_map(symbol.upper())
            return {"ok": True, "data": data}
        return {"ok": True, "data": {}}
    except Exception as e:
        logger.error(f"Liquidation map error: {e}")
        return {"ok": False, "data": {}}


@router.get("/assets")
async def get_supported_assets():
    """Get list of supported assets"""
    assets = getattr(oracle_engine, 'SUPPORTED_ASSETS', ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE'])
    return {
        "assets": assets,
        "model_version": getattr(oracle_engine, 'MODEL_VERSION', ORACLE_VERSION)
    }


@router.get("/status")
async def get_oracle_status():
    """Get ORACLE system status"""
    return {
        "status": "operational",
        "version": getattr(oracle_engine, 'MODEL_VERSION', ORACLE_VERSION),
        "institutional_grade": ORACLE_VERSION == "v3.0",
        "models_available": [
            "Time-Series Momentum (TSMOM)",
            "Mean Reversion (Bollinger)",
            "Sharpe Ratio",
            "Sortino Ratio", 
            "Value at Risk (VaR)",
            "On-Balance Volume",
            "Dual Moving Average",
            "RSI Divergence"
        ] if ORACLE_VERSION == "v3.0" else ["Basic ORACLE v2"]
    }
