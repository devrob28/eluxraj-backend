"""
Whale Intelligence API Endpoints - Gotham Intel
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.whale_intel import whale_intel_service
from app.core.logging import logger

router = APIRouter()


@router.get("/transfers")
async def get_live_transfers(limit: int = 50):
    """Get live whale transfers"""
    try:
        return await whale_intel_service.get_live_transfers(limit=limit)
    except Exception as e:
        logger.error(f"Error getting transfers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flows")
async def get_exchange_flows():
    """Get exchange inflow/outflow data"""
    try:
        return await whale_intel_service.get_exchange_flows()
    except Exception as e:
        logger.error(f"Error getting flows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights")
async def get_trending_insights():
    """Get AI-generated trending insights"""
    try:
        return await whale_intel_service.get_trending_insights()
    except Exception as e:
        logger.error(f"Error getting insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sentiment")
async def get_smart_money_sentiment():
    """Get smart money sentiment analysis"""
    try:
        return await whale_intel_service.get_smart_money_sentiment()
    except Exception as e:
        logger.error(f"Error getting sentiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def whale_intel_status():
    """Health check for whale intel service"""
    return {
        "ok": True,
        "service": "Gotham Intel",
        "version": "1.0.0",
        "features": ["live_transfers", "exchange_flows", "insights", "sentiment"]
    }
