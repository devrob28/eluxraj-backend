"""
Whale Intel API Endpoints - Using Alchemy
"""
from fastapi import APIRouter, Query
from typing import Optional
from app.services.alchemy_whale_service import alchemy_whale_service

router = APIRouter(prefix="", tags=["Whale Intel"])


@router.get("/transfers")
async def get_whale_transfers(limit: int = Query(default=20, le=50)):
    try:
        transfers = await alchemy_whale_service.get_whale_transfers(limit=limit)
        return {"ok": True, "transfers": transfers, "count": len(transfers), "source": "alchemy"}
    except Exception as e:
        return {"ok": False, "error": str(e), "transfers": [], "count": 0}


@router.get("/flows")
async def get_exchange_flows():
    try:
        flows = await alchemy_whale_service.get_exchange_flows()
        return {"ok": True, **flows}
    except Exception as e:
        return {"ok": False, "error": str(e), "exchanges": []}


@router.get("/insights")
async def get_whale_insights():
    try:
        insights = await alchemy_whale_service.get_insights()
        return {"ok": True, "insights": insights}
    except Exception as e:
        return {"ok": False, "error": str(e), "insights": []}


@router.get("/sentiment")
async def get_smart_money_sentiment():
    try:
        return await alchemy_whale_service.get_sentiment()
    except Exception as e:
        return {"ok": False, "error": str(e), "sentiment": "Unknown", "sentiment_score": 50}


@router.get("/solana")
async def get_solana_whales():
    return {
        "ok": True,
        "trending_tokens": [
            {"symbol": "BONK", "name": "Bonk", "price_change_24h": 12.5, "whale_buys": 15},
            {"symbol": "WIF", "name": "dogwifhat", "price_change_24h": -5.2, "whale_buys": 8},
            {"symbol": "POPCAT", "name": "Popcat", "price_change_24h": 25.8, "whale_buys": 22},
            {"symbol": "PNUT", "name": "Peanut", "price_change_24h": 45.2, "whale_buys": 35},
        ],
        "note": "Solana requires Helius API"
    }
