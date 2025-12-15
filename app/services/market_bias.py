"""
Market Bias Service - Daily AI insights for retention
Generates daily market bias, scenarios, and reasoning
"""
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.core.logging import logger

class MarketBiasService:
    """Generates daily market bias and scenarios"""
    
    COINGECKO_API = "https://api.coingecko.com/api/v3"
    
    async def get_market_data(self, symbol: str) -> Optional[Dict]:
        """Fetch current market data"""
        coin_map = {
            "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
            "XRP": "ripple", "DOGE": "dogecoin", "ADA": "cardano"
        }
        coin_id = coin_map.get(symbol.upper(), symbol.lower())
        
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{self.COINGECKO_API}/coins/{coin_id}",
                    params={"localization": "false", "tickers": "false", "community_data": "false"},
                    timeout=10.0
                )
                if r.status_code == 200:
                    data = r.json()
                    market = data.get("market_data", {})
                    return {
                        "price": market.get("current_price", {}).get("usd"),
                        "change_24h": market.get("price_change_percentage_24h"),
                        "change_7d": market.get("price_change_percentage_7d"),
                        "high_24h": market.get("high_24h", {}).get("usd"),
                        "low_24h": market.get("low_24h", {}).get("usd"),
                        "volume": market.get("total_volume", {}).get("usd"),
                        "market_cap": market.get("market_cap", {}).get("usd")
                    }
        except Exception as e:
            logger.error(f"Market data error: {e}")
        return None

    def calculate_bias(self, data: Dict) -> Dict:
        """Calculate market bias from data"""
        change_24h = data.get("change_24h", 0) or 0
        change_7d = data.get("change_7d", 0) or 0
        
        # Weighted score: 60% 24h, 40% 7d
        score = (change_24h * 0.6) + (change_7d * 0.4)
        
        if score > 3:
            bias = "Bullish"
            emoji = "🟢"
            strength = min(100, int(50 + score * 5))
        elif score < -3:
            bias = "Bearish"
            emoji = "🔴"
            strength = min(100, int(50 + abs(score) * 5))
        else:
            bias = "Neutral"
            emoji = "🟡"
            strength = 50
        
        return {
            "bias": bias,
            "emoji": emoji,
            "strength": strength,
            "score": round(score, 2)
        }

    def generate_scenarios(self, symbol: str, data: Dict, bias: Dict) -> list:
        """Generate AI scenarios based on market conditions"""
        price = data.get("price", 0)
        scenarios = []
        
        if bias["bias"] == "Bullish":
            scenarios = [
                {"type": "bull", "label": "Bull Case", "target": round(price * 1.08, 2), "probability": 55, "reasoning": f"Momentum continues with {data.get('change_24h', 0):.1f}% daily gain"},
                {"type": "base", "label": "Base Case", "target": round(price * 1.03, 2), "probability": 30, "reasoning": "Consolidation near current levels"},
                {"type": "bear", "label": "Bear Case", "target": round(price * 0.95, 2), "probability": 15, "reasoning": "Profit-taking pullback"}
            ]
        elif bias["bias"] == "Bearish":
            scenarios = [
                {"type": "bear", "label": "Bear Case", "target": round(price * 0.92, 2), "probability": 55, "reasoning": f"Selling pressure continues with {data.get('change_24h', 0):.1f}% daily drop"},
                {"type": "base", "label": "Base Case", "target": round(price * 0.97, 2), "probability": 30, "reasoning": "Stabilization at support"},
                {"type": "bull", "label": "Bull Case", "target": round(price * 1.05, 2), "probability": 15, "reasoning": "Oversold bounce"}
            ]
        else:
            scenarios = [
                {"type": "base", "label": "Base Case", "target": round(price * 1.01, 2), "probability": 50, "reasoning": "Range-bound trading continues"},
                {"type": "bull", "label": "Bull Case", "target": round(price * 1.05, 2), "probability": 25, "reasoning": "Breakout above resistance"},
                {"type": "bear", "label": "Bear Case", "target": round(price * 0.95, 2), "probability": 25, "reasoning": "Breakdown below support"}
            ]
        
        return scenarios

    def generate_reasoning(self, symbol: str, data: Dict, bias: Dict) -> str:
        """Generate AI reasoning explanation"""
        change_24h = data.get("change_24h", 0) or 0
        change_7d = data.get("change_7d", 0) or 0
        
        parts = [f"{symbol} is showing {bias['bias'].lower()} momentum."]
        
        if abs(change_24h) > 5:
            direction = "gained" if change_24h > 0 else "lost"
            parts.append(f"Price {direction} {abs(change_24h):.1f}% in the last 24 hours.")
        
        if abs(change_7d) > 10:
            direction = "up" if change_7d > 0 else "down"
            parts.append(f"Weekly trend is {direction} {abs(change_7d):.1f}%.")
        
        if bias["bias"] == "Bullish":
            parts.append("Consider entries on pullbacks to support.")
        elif bias["bias"] == "Bearish":
            parts.append("Exercise caution and consider reducing exposure.")
        else:
            parts.append("Wait for clearer direction before taking new positions.")
        
        return " ".join(parts)

    async def get_daily_brief(self, symbols: list = None) -> Dict:
        """Get complete daily brief for dashboard"""
        if not symbols:
            symbols = ["BTC", "ETH", "SOL"]
        
        assets = []
        overall_score = 0
        
        for symbol in symbols:
            data = await self.get_market_data(symbol)
            if data:
                bias = self.calculate_bias(data)
                scenarios = self.generate_scenarios(symbol, data, bias)
                reasoning = self.generate_reasoning(symbol, data, bias)
                
                assets.append({
                    "symbol": symbol,
                    "price": data.get("price"),
                    "change_24h": data.get("change_24h"),
                    "bias": bias,
                    "scenarios": scenarios,
                    "reasoning": reasoning
                })
                overall_score += bias["score"]
        
        # Overall market bias
        avg_score = overall_score / len(assets) if assets else 0
        if avg_score > 2:
            overall_bias = {"bias": "Bullish", "emoji": "🟢"}
        elif avg_score < -2:
            overall_bias = {"bias": "Bearish", "emoji": "🔴"}
        else:
            overall_bias = {"bias": "Neutral", "emoji": "🟡"}
        
        # Trading session
        hour = datetime.now(timezone.utc).hour
        if 0 <= hour < 8:
            session = {"name": "Asia", "emoji": "🌏", "status": "Active"}
        elif 8 <= hour < 14:
            session = {"name": "London", "emoji": "🌍", "status": "Active"}
        else:
            session = {"name": "New York", "emoji": "🌎", "status": "Active"}
        
        return {
            "ok": True,
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "session": session,
            "overall_bias": overall_bias,
            "assets": assets,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }


market_bias_service = MarketBiasService()
