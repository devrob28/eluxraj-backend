"""Trade Playbooks API - AI-Powered Decision Intelligence"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional

from app.db.session import get_db
from app.core.deps import get_current_user
from app.core.logging import logger
from app.models.playbook import TradePlaybook
from app.services.trade_intelligence import trade_intelligence
from app.services.rate_limiter import rate_limiter

router = APIRouter()


class PlaybookRequest(BaseModel):
    asset: str
    asset_type: str = None  # Auto-detect if not provided
    timeframe: str = "4h"


@router.get("/usage")
async def get_usage_stats(
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current API usage stats for the user"""
    stats = rate_limiter.get_usage(db, user.id, user.subscription_tier)
    return {
        "tier": user.subscription_tier,
        "usage": stats,
        "resets_at": "00:00 UTC"
    }


@router.get("/history")
async def get_playbook_history(
    user = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(20, le=100)
):
    """Get user playbook history (all status)"""
    playbooks = db.query(TradePlaybook).filter(
        TradePlaybook.user_id == user.id
    ).order_by(TradePlaybook.created_at.desc()).limit(limit).all()
    
    return {
        "count": len(playbooks),
        "playbooks": [_format_playbook(p) for p in playbooks]
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
    # Check rate limit (also checks tier access)
    usage_info = rate_limiter.check_and_increment(
        db=db,
        user_id=user.id,
        tier=user.subscription_tier,
        feature="playbook"
    )
    
    # Auto-detect asset type if not provided
    if not request.asset_type:
        symbol = request.asset.upper()
        # Known stock symbols (major ones)
        stocks = ["AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "NVDA", "TSLA", "AMD", "NFLX", "CRM", "ORCL", "IBM", "INTC", "CSCO", "ADBE", "PYPL", "SQ", "SHOP", "UBER", "ABNB", "COIN", "MSTR", "PLTR", "SNOW", "NET", "CRWD", "ZS", "DDOG", "MDB", "SPY", "QQQ", "DIA", "IWM", "VTI", "VOO", "JPM", "BAC", "WFC", "GS", "MS", "V", "MA", "AXP", "DIS", "NKE", "SBUX", "MCD", "WMT", "TGT", "COST", "HD", "LOW", "PG", "KO", "PEP", "JNJ", "PFE", "UNH", "MRNA", "LLY", "ABBV", "XOM", "CVX", "COP", "BA", "CAT", "DE", "GE", "MMM", "HON"]
        # If symbol looks like a stock or is in our list
        if symbol in stocks or (len(symbol) <= 5 and symbol.isalpha() and not symbol.endswith("USD") and not symbol.endswith("USDT")):
            request.asset_type = "stock"
        else:
            request.asset_type = "crypto"
        logger.info(f"Auto-detected asset type: {request.asset_type} for {symbol}")
    
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
            confidence_score=playbook_data.get("confidence_score", 0),
            bullish_scenarios=playbook_data.get("bullish_scenarios", []),
            bearish_scenarios=playbook_data.get("bearish_scenarios", []),
            invalidation_conditions=playbook_data.get("invalidation_conditions", []),
            invalidation_price=playbook_data.get("invalidation_price", 0),
            pattern_detected=playbook_data.get("pattern_detected", "none"),
            market_structure=playbook_data.get("market_structure", "unclear"),
            reasoning=playbook_data.get("reasoning", ""),
            status="active"
        )
        db.add(playbook)
        db.commit()
        db.refresh(playbook)
        playbook_id = playbook.id
    except Exception as e:
        logger.error(f"Failed to save playbook: {e}")
        playbook_id = None
    
    return {
        "playbook_id": playbook_id,
        "asset": request.asset.upper(),
        "asset_type": request.asset_type,
        "timeframe": request.timeframe,
        "current_price": current_price,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "usage": usage_info,
        **playbook_data,
        "disclaimer": "ELUXRAJ provides AI-powered decision intelligence for informational purposes only. This is NOT financial advice. All trading involves risk. Past performance does not guarantee future results."
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


async def _get_current_price(asset: str, asset_type: str) -> float:
    """Fetch current price from CoinGecko (crypto) or Yahoo Finance (stocks)"""
    import httpx
    
    if asset_type == "stock":
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # Use Yahoo Finance API
                r = await client.get(
                    f"https://query1.finance.yahoo.com/v8/finance/chart/{asset}",
                    headers={"User-Agent": "Mozilla/5.0"}
                )
                if r.status_code == 200:
                    data = r.json()
                    price = data.get("chart", {}).get("result", [{}])[0].get("meta", {}).get("regularMarketPrice", 0)
                    if price:
                        return float(price)
        except Exception as e:
            pass
        return 0
    
    """Fetch current price from CoinGecko or FMP"""
    import httpx
    
    if asset_type == "crypto":
        cg_id = _get_coingecko_id(asset)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"https://api.coingecko.com/api/v3/simple/price?ids={cg_id}&vs_currencies=usd")
                if r.status_code == 200:
                    data = r.json()
                    return data.get(cg_id, {}).get("usd", 0)
        except:
            pass
    return 0


async def _get_market_context(asset: str, asset_type: str) -> dict:
    """Get additional market context"""
    return {
        "asset": asset,
        "type": asset_type,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def _get_coingecko_id(symbol: str) -> str:
    """Map common symbols to CoinGecko IDs"""
    mapping = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
        "XRP": "ripple",
        "ADA": "cardano",
        "DOGE": "dogecoin",
        "DOT": "polkadot",
        "MATIC": "matic-network",
        "AVAX": "avalanche-2",
        "LINK": "chainlink",
        "UNI": "uniswap",
        "ATOM": "cosmos",
        "LTC": "litecoin",
        "BNB": "binancecoin",
    }
    return mapping.get(symbol.upper(), symbol.lower())


def _format_playbook(p: TradePlaybook) -> dict:
    """Format playbook for API response"""
    return {
        "id": p.id,
        "asset": p.asset,
        "asset_type": p.asset_type,
        "timeframe": p.timeframe,
        "market_bias": p.market_bias,
        "bias_strength": p.bias_strength,
        "entry_zone": {
            "low": p.entry_zone_low,
            "high": p.entry_zone_high
        },
        "stop_loss": p.stop_loss,
        "take_profits": [p.take_profit_1, p.take_profit_2, p.take_profit_3],
        "risk_reward_ratio": p.risk_reward_ratio,
        "probability_score": p.probability_score,
        "confidence_score": p.confidence_score,
        "bullish_scenarios": p.bullish_scenarios or [],
        "bearish_scenarios": p.bearish_scenarios or [],
        "invalidation_conditions": p.invalidation_conditions or [],
        "invalidation_price": p.invalidation_price,
        "pattern_detected": p.pattern_detected,
        "market_structure": p.market_structure,
        "status": p.status,
        "created_at": p.created_at.isoformat() if p.created_at else None
    }
