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


@router.get("/stock/{symbol}")
async def get_stock_oracle(
    symbol: str,
    user = Depends(require_elite)
):
    """
    Get ORACLE signal for a stock
    Uses Yahoo Finance for stock data
    """
    import httpx
    from datetime import datetime, timedelta
    
    try:
        # Fetch stock data from Yahoo Finance
        async with httpx.AsyncClient() as client:
            # Get quote data
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=30d"
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            data = resp.json()
            
            if "chart" not in data or not data["chart"]["result"]:
                raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
            
            result = data["chart"]["result"][0]
            meta = result["meta"]
            quote = result["indicators"]["quote"][0]
            
            current_price = meta.get("regularMarketPrice", 0)
            prev_close = meta.get("previousClose", current_price)
            change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
            
            # Calculate simple technical score
            closes = quote.get("close", [])
            closes = [c for c in closes if c is not None]
            
            if len(closes) >= 5:
                sma5 = sum(closes[-5:]) / 5
                sma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else sma5
                
                # Simple scoring
                trend_score = 60 if current_price > sma5 else 40
                momentum_score = 60 if sma5 > sma20 else 40
                volatility = max(closes[-5:]) - min(closes[-5:])
                vol_score = 50 if volatility / current_price < 0.05 else 40
                
                oracle_score = int((trend_score + momentum_score + vol_score) / 3)
            else:
                oracle_score = 50
            
            # Determine signal
            if oracle_score >= 60:
                signal_type = "buy"
                confidence = "high" if oracle_score >= 70 else "medium"
            elif oracle_score <= 40:
                signal_type = "sell"
                confidence = "high" if oracle_score <= 30 else "medium"
            else:
                signal_type = "hold"
                confidence = "low"
            
            target_pct = 5
            stop_pct = 3
            
            return {
                "ok": True,
                "data": {
                    "asset_type": "stock",
                    "symbol": symbol.upper(),
                    "signal_type": signal_type,
                    "oracle_score": oracle_score,
                    "confidence": confidence,
                    "price": current_price,
                    "entry_price": current_price,
                    "target_price": current_price * (1 + target_pct / 100),
                    "stop_loss": current_price * (1 - stop_pct / 100),
                    "target_pct": target_pct,
                    "stop_pct": stop_pct,
                    "risk_reward_ratio": round(target_pct / stop_pct, 1),
                    "price_change_24h": round(change_pct, 2),
                    "factor_breakdown": [
                        {"name": "trend", "score": trend_score if 'trend_score' in dir() else 50, "value": "bullish" if oracle_score > 50 else "bearish"},
                        {"name": "momentum", "score": momentum_score if 'momentum_score' in dir() else 50, "value": "positive" if oracle_score > 50 else "negative"},
                        {"name": "volatility", "score": vol_score if 'vol_score' in dir() else 50, "value": "moderate"},
                    ],
                    "reasoning_summary": f"{signal_type.upper()} - {symbol} ORACLE Score: {oracle_score}/100",
                    "reasoning_bullets": [
                        f"Current price: ${current_price:.2f}",
                        f"24h change: {change_pct:+.2f}%"
                    ],
                    "model_version": "oracle-stock-v1.0"
                },
                "tier": user.subscription_tier
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stock oracle error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze {symbol}")
