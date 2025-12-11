"""
ORACLE API Endpoints - v3.0 Institutional Grade
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app.core.deps import get_current_user, require_elite
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
    """Get full ORACLE analysis for a crypto asset"""
    try:
        signal = await oracle_engine.generate_signal(symbol.upper())
        
        if not signal:
            raise HTTPException(status_code=404, detail=f"Unable to generate signal for {symbol}")
        
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


@router.get("/stock/{symbol}")
async def get_stock_oracle(
    symbol: str,
    user = Depends(require_elite)
):
    """Get ORACLE signal for a stock using Yahoo Finance"""
    import httpx
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
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
            
            closes = [c for c in quote.get("close", []) if c is not None]
            
            trend_score = 50
            momentum_score = 50
            vol_score = 50
            
            if len(closes) >= 5:
                sma5 = sum(closes[-5:]) / 5
                sma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else sma5
                trend_score = 65 if current_price > sma5 else 35
                momentum_score = 65 if sma5 > sma20 else 35
                volatility = (max(closes[-5:]) - min(closes[-5:])) / current_price if current_price else 0
                vol_score = 60 if volatility < 0.05 else 40
            
            oracle_score = int((trend_score + momentum_score + vol_score) / 3)
            
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
                    "target_price": round(current_price * (1 + target_pct / 100), 2),
                    "stop_loss": round(current_price * (1 - stop_pct / 100), 2),
                    "target_pct": target_pct,
                    "stop_pct": stop_pct,
                    "risk_reward_ratio": round(target_pct / stop_pct, 1),
                    "price_change_24h": round(change_pct, 2),
                    "factor_breakdown": [
                        {"name": "trend", "score": trend_score, "value": "bullish" if trend_score > 50 else "bearish"},
                        {"name": "momentum", "score": momentum_score, "value": "positive" if momentum_score > 50 else "negative"},
                        {"name": "volatility", "score": vol_score, "value": "low" if vol_score > 50 else "high"},
                    ],
                    "reasoning_summary": f"{signal_type.upper()} - {symbol.upper()} ORACLE Score: {oracle_score}/100",
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


@router.get("/demo/{symbol}")
async def get_oracle_demo(symbol: str):
    """Get demo ORACLE data for non-Elite users"""
    try:
        signal = await oracle_engine.generate_signal(symbol.upper())
        if not signal:
            return {"ok": False, "message": "Unable to generate demo signal"}
        
        return {
            "ok": True,
            "demo": True,
            "data": {
                "symbol": signal.get("symbol"),
                "oracle_score": signal.get("oracle_score"),
                "signal_type": signal.get("signal_type"),
                "confidence": signal.get("confidence"),
                "price": signal.get("price") or signal.get("entry_price"),
                "message": "Upgrade to Elite for full analysis"
            }
        }
    except Exception as e:
        logger.error(f"Demo oracle error: {e}")
        return {"ok": False, "message": "Demo unavailable"}


@router.get("/scan")
async def scan_all_assets():
    """Scan top assets"""
    try:
        signals = []
        for symbol in ['BTC', 'ETH', 'SOL']:
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
    return {"ok": True, "alerts": []}


@router.get("/liquidation-map/{symbol}")
async def get_liquidation_map(symbol: str):
    """Get liquidation heatmap"""
    return {"ok": True, "data": {}}


@router.get("/assets")
async def get_supported_assets():
    """Get list of supported assets"""
    return {
        "crypto": ["BTC", "ETH", "SOL"],
        "stocks": ["AAPL", "MSFT", "NVDA", "TSLA", "GOOGL", "AMZN", "META", "AMD", "NFLX", "JPM", 
                   "V", "JNJ", "WMT", "PG", "MA", "UNH", "HD", "DIS", "BAC", "XOM", "KO", "PFE", "INTC", "CSCO", "VZ"],
        "model_version": ORACLE_VERSION
    }


@router.get("/status")
async def get_oracle_status():
    """Get ORACLE system status"""
    return {
        "status": "operational",
        "version": ORACLE_VERSION,
        "supported_assets": {
            "crypto": 3,
            "stocks": 25
        }
    }
