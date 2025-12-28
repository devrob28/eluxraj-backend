"""
APEX Whale Intel API Endpoints
Institutional-grade whale tracking for Crypto AND Stocks
"""
from fastapi import APIRouter, Query, Depends
from typing import Optional
from app.services.apex_whale_intel import apex_whale_intel
from app.services.alchemy_whale_service import alchemy_whale_service
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="", tags=["Whale Intel"])


@router.get("/feed")
async def get_unified_whale_feed(
    limit: int = Query(default=50, le=100),
    asset_type: Optional[str] = Query(default=None, description="crypto or stock"),
    
):
    """Get unified whale feed - crypto whales + stock insiders"""
    try:
        feed = await apex_whale_intel.get_unified_whale_feed(limit=limit)
        
        if asset_type:
            feed["transactions"] = [
                t for t in feed["transactions"] 
                if t.get("asset_type") == asset_type
            ]
            feed["summary"]["filtered_by"] = asset_type
        
        return feed
    except Exception as e:
        return {"ok": False, "error": str(e), "transactions": []}


@router.get("/transfers")
async def get_whale_transfers(limit: int = Query(default=20, le=50)):
    """Get crypto whale transfers (legacy endpoint)"""
    try:
        transfers = await alchemy_whale_service.get_whale_transfers(limit=limit)
        return {"ok": True, "transfers": transfers, "count": len(transfers), "source": "alchemy"}
    except Exception as e:
        return {"ok": False, "error": str(e), "transfers": [], "count": 0}


@router.get("/crypto")
async def get_crypto_whale_activity(
    limit: int = Query(default=25, le=50),
    
):
    """Get crypto whale activity from exchanges and market makers"""
    try:
        activity = await apex_whale_intel.get_crypto_whale_activity(limit=limit)
        return {"ok": True, "transactions": activity, "count": len(activity), "asset_type": "crypto"}
    except Exception as e:
        return {"ok": False, "error": str(e), "transactions": []}


@router.get("/stocks")
async def get_stock_insider_activity(
    limit: int = Query(default=25, le=50),
    ticker: Optional[str] = Query(default=None, description="Filter by stock ticker"),
    
):
    """Get stock insider trading from SEC Form 4 filings"""
    try:
        activity = await apex_whale_intel.get_stock_insider_activity(limit=limit, ticker=ticker)
        return {"ok": True, "transactions": activity, "count": len(activity), "asset_type": "stock"}
    except Exception as e:
        return {"ok": False, "error": str(e), "transactions": []}


@router.get("/insider-buys")
async def get_top_insider_buys(
    days: int = Query(default=7, le=30),
    
):
    """Get top insider buys - bullish signal when executives buy their own stock"""
    try:
        buys = await apex_whale_intel.get_top_insider_buys(days=days)
        return {"ok": True, "buys": buys, "count": len(buys), "days": days}
    except Exception as e:
        return {"ok": False, "error": str(e), "buys": []}


@router.get("/flows")
async def get_exchange_flows():
    """Get exchange inflow/outflow analysis"""
    try:
        flows = await apex_whale_intel.get_exchange_flows()
        return flows
    except Exception as e:
        return {"ok": False, "error": str(e), "exchanges": []}


@router.get("/insights")
async def get_whale_insights():
    """Get actionable whale insights combining crypto and stocks"""
    try:
        insights = await apex_whale_intel.get_whale_insights()
        return {"ok": True, "insights": insights, "count": len(insights)}
    except Exception as e:
        return {"ok": False, "error": str(e), "insights": []}


@router.get("/sentiment")
async def get_whale_sentiment():
    """Get overall smart money sentiment score"""
    try:
        feed = await apex_whale_intel.get_unified_whale_feed(limit=50)
        summary = feed.get("summary", {})
        
        crypto = summary.get("crypto", {})
        stocks = summary.get("stocks", {})
        
        total_bullish = crypto.get("bullish", 0) + stocks.get("bullish", 0)
        total_bearish = crypto.get("bearish", 0) + stocks.get("bearish", 0)
        total = total_bullish + total_bearish
        
        score = int((total_bullish / total) * 100) if total > 0 else 50
        
        if score >= 60:
            sentiment, emoji = "Bullish", "🟢"
        elif score <= 40:
            sentiment, emoji = "Bearish", "🔴"
        else:
            sentiment, emoji = "Neutral", "🟡"
        
        return {
            "ok": True,
            "sentiment": sentiment,
            "sentiment_emoji": emoji,
            "sentiment_score": score,
            "crypto": {
                "sentiment": crypto.get("sentiment", "neutral"),
                "bullish": crypto.get("bullish", 0),
                "bearish": crypto.get("bearish", 0)
            },
            "stocks": {
                "sentiment": stocks.get("sentiment", "neutral"),
                "bullish": stocks.get("bullish", 0),
                "bearish": stocks.get("bearish", 0)
            },
            "last_updated": feed.get("last_updated")
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "sentiment": "Unknown", "sentiment_score": 50}


@router.get("/solana")
async def get_solana_whales():
    """Solana whale tracking (coming soon)"""
    return {
        "ok": True,
        "trending_tokens": [
            {"symbol": "BONK", "name": "Bonk", "price_change_24h": 12.5, "whale_buys": 15},
            {"symbol": "WIF", "name": "dogwifhat", "price_change_24h": -5.2, "whale_buys": 8},
            {"symbol": "POPCAT", "name": "Popcat", "price_change_24h": 25.8, "whale_buys": 22},
        ],
        "note": "Full Solana tracking coming soon - requires Helius API"
    }
