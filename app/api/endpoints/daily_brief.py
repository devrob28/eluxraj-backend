"""
Daily Brief API - Market Bias & Scenarios for Dashboard Ritual
"""
from fastapi import APIRouter, Depends
from app.services.market_bias import market_bias_service
from app.core.deps import get_current_user

router = APIRouter()

@router.get("")
async def get_daily_brief(user=Depends(get_current_user)):
    """Get daily market brief for dashboard ritual"""
    # All tiers get basic brief, Elite gets more assets
    symbols = ["BTC", "ETH", "SOL"]
    if user.subscription_tier == "elite":
        symbols.extend(["XRP", "DOGE", "ADA"])
    
    brief = await market_bias_service.get_daily_brief(symbols)
    brief["tier"] = user.subscription_tier
    return brief

@router.get("/public")
async def get_public_brief():
    """Public brief with limited data (for marketing)"""
    brief = await market_bias_service.get_daily_brief(["BTC"])
    # Remove scenarios for public
    for asset in brief.get("assets", []):
        asset["scenarios"] = [asset["scenarios"][0]] if asset.get("scenarios") else []
        asset["reasoning"] = asset["reasoning"].split(".")[0] + "."
    return brief
