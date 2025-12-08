"""
ORACLE API Endpoints - Elite-only ($98/mo)
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import datetime
from app.services.oracle import oracle

router = APIRouter()


@router.get("/score/{symbol}")
async def get_oracle_score(symbol: str):
    """Get full ORACLE analysis for an asset"""
    signal = await oracle.generate_signal(symbol.upper())
    
    if not signal:
        raise HTTPException(status_code=404, detail=f"Could not analyze {symbol}")
    
    return {
        "ok": True,
        "data": signal,
        "tier": "elite",
        "model_version": signal.get("model_version"),
    }


@router.get("/demo/{symbol}")
async def get_oracle_demo(symbol: str):
    """Get demo ORACLE data for non-Elite users"""
    signal = await oracle.generate_signal(symbol.upper())
    
    if not signal:
        raise HTTPException(status_code=404, detail=f"Could not analyze {symbol}")
    
    return {
        "ok": True,
        "data": {
            "symbol": signal["symbol"],
            "oracle_score": "locked",
            "signal_type": "locked",
            "confidence": "locked",
            "entry_price": signal["entry_price"],
            "target_price": "locked",
            "stop_loss": "locked",
            "risk_reward_ratio": "locked",
            "reasoning_summary": "Upgrade to Elite to unlock full ORACLE predictions",
            "reasoning_bullets": [
                "Whale activity analysis locked",
                "Liquidation zones locked",
                "Smart entry points locked",
            ],
            "factor_breakdown": [
                {"name": "whale_activity", "score": "locked", "value": "locked"},
                {"name": "liquidation_risk", "score": "locked", "value": "locked"},
                {"name": "funding_rate", "score": "locked", "value": "locked"},
            ],
            "is_demo": True,
            "upgrade_message": "Unlock full ORACLE predictions with Elite subscription - $98/mo",
            "upgrade_url": "/pricing.html",
        },
        "tier": "demo",
    }


@router.get("/scan")
async def scan_all_assets():
    """Scan all supported assets"""
    signals = await oracle.scan_all_assets()
    
    return {
        "ok": True,
        "data": signals,
        "count": len(signals),
        "scanned_at": datetime.utcnow().isoformat(),
    }


@router.get("/whale-alerts/{symbol}")
async def get_whale_alerts(symbol: str):
    """Get whale alerts for an asset"""
    alerts = await oracle.get_whale_alerts(symbol.upper())
    
    return {
        "ok": True,
        "symbol": symbol.upper(),
        "alerts": alerts,
        "count": len(alerts),
    }


@router.get("/liquidation-map/{symbol}")
async def get_liquidation_map(symbol: str):
    """Get liquidation heatmap"""
    data = await oracle.get_liquidation_map(symbol.upper())
    
    if not data:
        raise HTTPException(status_code=404, detail=f"Could not get data for {symbol}")
    
    return {
        "ok": True,
        "symbol": symbol.upper(),
        "data": data,
    }


@router.get("/assets")
async def get_supported_assets():
    """Get list of supported assets"""
    return {
        "ok": True,
        "assets": [
            {"id": "BTC", "name": "Bitcoin", "icon": "₿"},
            {"id": "ETH", "name": "Ethereum", "icon": "Ξ"},
            {"id": "SOL", "name": "Solana", "icon": "◎"},
            {"id": "BNB", "name": "BNB", "icon": "⬡"},
            {"id": "XRP", "name": "XRP", "icon": "✕"},
            {"id": "ADA", "name": "Cardano", "icon": "₳"},
            {"id": "DOGE", "name": "Dogecoin", "icon": "Ð"},
            {"id": "AVAX", "name": "Avalanche", "icon": "△"},
            {"id": "DOT", "name": "Polkadot", "icon": "●"},
            {"id": "MATIC", "name": "Polygon", "icon": "⬡"},
            {"id": "LINK", "name": "Chainlink", "icon": "⬡"},
            {"id": "UNI", "name": "Uniswap", "icon": "🦄"},
            {"id": "PEPE", "name": "Pepe", "icon": "🐸"},
            {"id": "SHIB", "name": "Shiba Inu", "icon": "🐕"},
        ],
    }


@router.get("/status")
async def get_oracle_status():
    """Get ORACLE system status"""
    return {
        "ok": True,
        "status": "operational",
        "version": oracle.MODEL_VERSION,
        "features": [
            "whale-tracking",
            "liquidation-zones", 
            "funding-rates",
            "exchange-flow",
            "open-interest",
            "social-sentiment",
        ],
        "supported_assets": len(oracle.SUPPORTED_ASSETS),
        "elite_required": True,
        "price": "$98/mo",
    }
