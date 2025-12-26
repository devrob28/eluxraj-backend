"""Trade Playbook API - Institutional Grade Decision Intelligence"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel

from app.db.session import get_db
from app.core.deps import get_current_user
from app.core.logging import logger
from app.services.trade_intelligence import trade_intelligence
from app.models.playbook import TradePlaybook

router = APIRouter()

class PlaybookRequest(BaseModel):
    asset: str
    asset_type: str = "crypto"  # crypto, stock, forex
    timeframe: str = "4h"

@router.post("/generate")
async def generate_playbook(
    request: PlaybookRequest,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate an AI Trade Playbook with:
    - Market Bias & Entry Zone
    - Stop Loss & Take Profit Targets
    - 3 Bullish + 3 Bearish Scenarios with probabilities
    - Invalidation Conditions
    - Confidence & Risk Metrics
    """
    # Check tier access
    if user.subscription_tier not in ["pro", "elite", "admin"]:
        raise HTTPException(status_code=403, detail="Pro or Elite subscription required for Trade Playbooks")
    
    # Get current price
    current_price = await _get_current_price(request.asset, request.asset_type)
    
    # Get market data for context
    market_data = await _get_market_context(request.asset, request.asset_type)
    
    # Generate playbook via AI
    logger.info(f"Generating playbook for {request.asset} ({request.timeframe})")
    playbook_data = await trade_intelligence.generate_playbook(
        asset=request.asset,
        asset_type=request.asset_type,
        timeframe=request.timeframe,
        current_price=current_price,
        market_data=market_data
    )
    
    # Save to database
    try:
        playbook = TradePlaybook(
            user_id=user.id,
            asset=request.asset.upper(),
            asset_type=request.asset_type,
            timeframe=request.timeframe,
            market_bias=playbook_data.get("market_bias", "neutral"),
            bias_strength=playbook_data.get("bias_strength", 50),
            entry_zone_low=playbook_data.get("entry_zone", {}).get("low", 0),
            entry_zone_high=playbook_data.get("entry_zone", {}).get("high", 0),
            stop_loss=playbook_data.get("stop_loss", {}).get("price", 0),
            take_profit_1=playbook_data.get("take_profits", [{}])[0].get("price", 0) if playbook_data.get("take_profits") else 0,
            take_profit_2=playbook_data.get("take_profits", [{}, {}])[1].get("price", 0) if len(playbook_data.get("take_profits", [])) > 1 else 0,
            take_profit_3=playbook_data.get("take_profits", [{}, {}, {}])[2].get("price", 0) if len(playbook_data.get("take_profits", [])) > 2 else 0,
            risk_reward_ratio=playbook_data.get("risk_reward_ratio", 0),
            probability_score=playbook_data.get("probability_score", 50),
            confidence_score=playbook_data.get("confidence_score", 50),
            bullish_scenarios=playbook_data.get("bullish_scenarios", []),
            bearish_scenarios=playbook_data.get("bearish_scenarios", []),
            invalidation_conditions=playbook_data.get("invalidation_conditions", []),
            invalidation_price=playbook_data.get("invalidation_price"),
            pattern_detected=playbook_data.get("pattern_detected"),
            market_structure=playbook_data.get("market_structure"),
            reasoning=playbook_data.get("reasoning")
        )
        db.add(playbook)
        db.commit()
        db.refresh(playbook)
        playbook_id = playbook.id
    except Exception as e:
        logger.error(f"Failed to save playbook: {e}")
        db.rollback()
        playbook_id = None
    
    return {
        "playbook_id": playbook_id,
        "asset": request.asset.upper(),
        "asset_type": request.asset_type,
        "timeframe": request.timeframe,
        "current_price": current_price,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "market_bias": playbook_data.get("market_bias"),
        "bias_strength": playbook_data.get("bias_strength"),
        "entry_zone": playbook_data.get("entry_zone"),
        "stop_loss": playbook_data.get("stop_loss"),
        "take_profits": playbook_data.get("take_profits"),
        "risk_reward_ratio": playbook_data.get("risk_reward_ratio"),
        "probability_score": playbook_data.get("probability_score"),
        "confidence_score": playbook_data.get("confidence_score"),
        "bullish_scenarios": playbook_data.get("bullish_scenarios"),
        "bearish_scenarios": playbook_data.get("bearish_scenarios"),
        "invalidation_conditions": playbook_data.get("invalidation_conditions"),
        "invalidation_price": playbook_data.get("invalidation_price"),
        "pattern_detected": playbook_data.get("pattern_detected"),
        "market_structure": playbook_data.get("market_structure"),
        "reasoning": playbook_data.get("reasoning"),
        "disclaimer": "ELUXRAJ provides AI-powered decision intelligence for informational purposes only. This is NOT financial advice. All trading involves risk. Past performance does not guarantee future results."
    }

@router.get("/active")
async def get_active_playbooks(
    user = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(10, le=50)
):
    """Get user's active playbooks"""
    playbooks = db.query(TradePlaybook).filter(
        TradePlaybook.user_id == user.id,
        TradePlaybook.status == "active"
    ).order_by(TradePlaybook.created_at.desc()).limit(limit).all()
    
    return {
        "count": len(playbooks),
        "playbooks": [_format_playbook(p) for p in playbooks]
    }

@router.get("/{playbook_id}")
async def get_playbook(
    playbook_id: int,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific playbook"""
    playbook = db.query(TradePlaybook).filter(
        TradePlaybook.id == playbook_id,
        TradePlaybook.user_id == user.id
    ).first()
    
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    
    return _format_playbook(playbook)

def _format_playbook(p: TradePlaybook) -> dict:
    return {
        "id": p.id,
        "asset": p.asset,
        "asset_type": p.asset_type,
        "timeframe": p.timeframe,
        "market_bias": p.market_bias,
        "bias_strength": p.bias_strength,
        "entry_zone": {"low": p.entry_zone_low, "high": p.entry_zone_high},
        "stop_loss": p.stop_loss,
        "take_profits": [p.take_profit_1, p.take_profit_2, p.take_profit_3],
        "risk_reward_ratio": p.risk_reward_ratio,
        "probability_score": p.probability_score,
        "confidence_score": p.confidence_score,
        "bullish_scenarios": p.bullish_scenarios,
        "bearish_scenarios": p.bearish_scenarios,
        "invalidation_conditions": p.invalidation_conditions,
        "invalidation_price": p.invalidation_price,
        "pattern_detected": p.pattern_detected,
        "market_structure": p.market_structure,
        "status": p.status,
        "created_at": p.created_at.isoformat() if p.created_at else None
    }

async def _get_current_price(asset: str, asset_type: str) -> float:
    """Fetch current price for asset"""
    import httpx
    try:
        if asset_type == "crypto":
            symbol = asset.upper().replace("-", "").replace("/", "")
            if not symbol.endswith("USDT"):
                symbol = symbol.replace("USD", "") + "USDT"
            async with httpx.AsyncClient() as client:
                r = await client.get(f"https://api.coingecko.com/api/v3/simple/price?ids={_get_coingecko_id(asset)}&vs_currencies=usd")
                if r.status_code == 200:
                    data = r.json()
                    coin_id = _get_coingecko_id(asset)
                    if coin_id in data:
                        return data[coin_id]["usd"]
        else:  # stock
            async with httpx.AsyncClient() as client:
                r = await client.get(f"https://financialmodelingprep.com/api/v3/quote/{asset}?apikey=demo")
                if r.status_code == 200:
                    data = r.json()
                    if data and len(data) > 0:
                        return data[0].get("price", 0)
    except Exception as e:
        logger.error(f"Price fetch failed: {e}")
    return 0

def _get_coingecko_id(asset: str) -> str:
    """Map asset symbol to CoinGecko ID"""
    mapping = {
        "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
        "XRP": "ripple", "DOGE": "dogecoin", "ADA": "cardano",
        "AVAX": "avalanche-2", "LINK": "chainlink", "DOT": "polkadot"
    }
    symbol = asset.upper().replace("-USD", "").replace("USDT", "").replace("/", "")
    return mapping.get(symbol, symbol.lower())

async def _get_market_context(asset: str, asset_type: str) -> dict:
    """Get additional market context"""
    return {
        "asset": asset,
        "type": asset_type,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
