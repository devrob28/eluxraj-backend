"""
Enhanced Data Providers for ORACLE v2.0
"""
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.core.logging import logger

class CoinGeckoProvider:
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    SYMBOL_MAP = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
        "BNB": "binancecoin",
        "XRP": "ripple",
        "ADA": "cardano",
        "DOGE": "dogecoin",
        "AVAX": "avalanche-2",
        "DOT": "polkadot",
        "MATIC": "matic-network",
        "LINK": "chainlink",
        "UNI": "uniswap",
        "PEPE": "pepe",
        "SHIB": "shiba-inu",
        "SPX": "s-p-500",
        "DJI": "dow-jones",
        "NDX": "nasdaq",
        "GOLD": "tether-gold",
        "SILVER": "silver",
    }
    
    async def get_price_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        coin_id = self.SYMBOL_MAP.get(symbol.upper())
        if not coin_id:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.BASE_URL}/coins/{coin_id}",
                    params={
                        "localization": "false",
                        "tickers": "false",
                        "market_data": "true",
                        "community_data": "true",
                        "developer_data": "false",
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"CoinGecko error: {response.status_code}")
                    return None
                
                data = response.json()
                market = data.get("market_data", {})
                
                return {
                    "symbol": symbol.upper(),
                    "current_price": market.get("current_price", {}).get("usd"),
                    "market_cap": market.get("market_cap", {}).get("usd"),
                    "volume_24h": market.get("total_volume", {}).get("usd"),
                    "price_change_24h": market.get("price_change_percentage_24h"),
                    "price_change_7d": market.get("price_change_percentage_7d"),
                    "price_change_30d": market.get("price_change_percentage_30d"),
                    "high_24h": market.get("high_24h", {}).get("usd"),
                    "low_24h": market.get("low_24h", {}).get("usd"),
                    "ath": market.get("ath", {}).get("usd"),
                    "ath_change_percentage": market.get("ath_change_percentage", {}).get("usd"),
                    "circulating_supply": market.get("circulating_supply"),
                    "total_supply": market.get("total_supply"),
                    "twitter_followers": data.get("community_data", {}).get("twitter_followers"),
                    "reddit_subscribers": data.get("community_data", {}).get("reddit_subscribers"),
                    "sentiment_votes_up": data.get("sentiment_votes_up_percentage"),
                    "sentiment_votes_down": data.get("sentiment_votes_down_percentage"),
                }
                
        except Exception as e:
            logger.error(f"CoinGecko fetch error: {e}")
            return None
    
    async def get_market_chart(self, symbol: str, days: int = 7) -> Optional[Dict[str, Any]]:
        coin_id = self.SYMBOL_MAP.get(symbol.upper())
        if not coin_id:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.BASE_URL}/coins/{coin_id}/market_chart",
                    params={"vs_currency": "usd", "days": days}
                )
                
                if response.status_code != 200:
                    return None
                
                return response.json()
                
        except Exception as e:
            logger.error(f"CoinGecko chart error: {e}")
            return None


class FearGreedProvider:
    BASE_URL = "https://api.alternative.me/fng/"
    
    async def get_current(self) -> Optional[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(self.BASE_URL, params={"limit": 1})
                
                if response.status_code != 200:
                    return None
                
                data = response.json()
                if data.get("data"):
                    item = data["data"][0]
                    return {
                        "value": int(item.get("value", 50)),
                        "classification": item.get("value_classification", "Neutral"),
                        "timestamp": item.get("timestamp"),
                    }
                return None
                
        except Exception as e:
            logger.error(f"Fear & Greed fetch error: {e}")
            return None


class WhaleAlertProvider:
    async def get_whale_activity(self, symbol: str, price_data: Dict) -> Dict[str, Any]:
        volume_24h = price_data.get("volume_24h", 0) or 0
        market_cap = price_data.get("market_cap", 1) or 1
        price_change = price_data.get("price_change_24h", 0) or 0
        
        volume_ratio = (volume_24h / market_cap) * 100 if market_cap > 0 else 0
        
        whale_score = 50
        whale_signals = []
        activity_type = "neutral"
        
        if volume_ratio > 15 and price_change > 2:
            whale_score = 85
            activity_type = "heavy_accumulation"
            whale_signals.append({
                "type": "accumulation",
                "title": "Whale Accumulation Detected",
                "description": f"Volume surge {volume_ratio:.1f}% of market cap with +{price_change:.1f}% price",
                "impact": "bullish",
                "timestamp": datetime.utcnow().isoformat()
            })
        elif volume_ratio > 15 and price_change < -2:
            whale_score = 25
            activity_type = "heavy_distribution"
            whale_signals.append({
                "type": "distribution",
                "title": "Whale Distribution Alert",
                "description": f"Volume surge {volume_ratio:.1f}% of market cap with {price_change:.1f}% price drop",
                "impact": "bearish",
                "timestamp": datetime.utcnow().isoformat()
            })
        elif volume_ratio > 8 and price_change > 1:
            whale_score = 70
            activity_type = "accumulating"
            whale_signals.append({
                "type": "accumulation",
                "title": "Whale Activity",
                "description": "Above average volume with bullish price action",
                "impact": "bullish",
                "timestamp": datetime.utcnow().isoformat()
            })
        elif volume_ratio > 8 and price_change < -1:
            whale_score = 35
            activity_type = "distributing"
            whale_signals.append({
                "type": "distribution",
                "title": "Whale Selling",
                "description": "Above average volume with bearish price action",
                "impact": "bearish",
                "timestamp": datetime.utcnow().isoformat()
            })
        elif volume_ratio < 3:
            whale_score = 50
            activity_type = "quiet"
        
        return {
            "score": whale_score,
            "activity_type": activity_type,
            "volume_ratio": round(volume_ratio, 2),
            "signals": whale_signals,
            "last_updated": datetime.utcnow().isoformat()
        }


class LiquidationProvider:
    async def get_liquidation_data(self, symbol: str, price_data: Dict, chart_data: Dict) -> Dict[str, Any]:
        current_price = price_data.get("current_price", 0)
        high_24h = price_data.get("high_24h", 0) or current_price
        low_24h = price_data.get("low_24h", 0) or current_price
        
        if not current_price:
            return {"score": 50, "risk_level": "unknown", "zones": []}
        
        price_range = high_24h - low_24h
        volatility_pct = (price_range / current_price) * 100 if current_price else 0
        
        zones = [
            {"type": "long", "price": round(current_price * 0.95, 2), "intensity": "high", "leverage": "10x"},
            {"type": "long", "price": round(current_price * 0.90, 2), "intensity": "medium", "leverage": "5x"},
            {"type": "long", "price": round(current_price * 0.85, 2), "intensity": "low", "leverage": "3x"},
            {"type": "short", "price": round(current_price * 1.05, 2), "intensity": "high", "leverage": "10x"},
            {"type": "short", "price": round(current_price * 1.10, 2), "intensity": "medium", "leverage": "5x"},
            {"type": "short", "price": round(current_price * 1.15, 2), "intensity": "low", "leverage": "3x"},
        ]
        
        if volatility_pct > 10:
            risk_score = 85
            risk_level = "extreme"
        elif volatility_pct > 7:
            risk_score = 70
            risk_level = "high"
        elif volatility_pct > 4:
            risk_score = 50
            risk_level = "moderate"
        else:
            risk_score = 30
            risk_level = "low"
        
        return {
            "score": risk_score,
            "risk_level": risk_level,
            "volatility_24h": round(volatility_pct, 2),
            "zones": zones,
            "estimated_liquidations_24h": round(volatility_pct * 50_000_000, 0),
            "nearest_long_liq": round(current_price * 0.95, 2),
            "nearest_short_liq": round(current_price * 1.05, 2),
        }


class FundingRateProvider:
    async def get_funding_data(self, symbol: str, price_data: Dict) -> Dict[str, Any]:
        price_change_24h = price_data.get("price_change_24h", 0) or 0
        
        if price_change_24h > 5:
            estimated_funding = 0.05
            sentiment = "extreme_long"
            score = 30
        elif price_change_24h > 2:
            estimated_funding = 0.02
            sentiment = "long_heavy"
            score = 45
        elif price_change_24h > -2:
            estimated_funding = 0.01
            sentiment = "balanced"
            score = 60
        elif price_change_24h > -5:
            estimated_funding = -0.02
            sentiment = "short_heavy"
            score = 70
        else:
            estimated_funding = -0.05
            sentiment = "extreme_short"
            score = 80
        
        return {
            "score": score,
            "estimated_funding_8h": round(estimated_funding, 4),
            "annualized_rate": round(estimated_funding * 3 * 365, 2),
            "sentiment": sentiment,
            "long_short_ratio": 1.5 if estimated_funding > 0.03 else 1.0 if estimated_funding > -0.01 else 0.7,
        }


class ExchangeFlowProvider:
    async def get_exchange_flow(self, symbol: str, price_data: Dict) -> Dict[str, Any]:
        volume_24h = price_data.get("volume_24h", 0) or 0
        market_cap = price_data.get("market_cap", 1) or 1
        price_change = price_data.get("price_change_24h", 0) or 0
        
        volume_ratio = (volume_24h / market_cap) * 100 if market_cap > 0 else 0
        
        if volume_ratio > 10 and price_change < -3:
            flow_type = "heavy_inflow"
            score = 25
            net_flow = volume_24h * 0.3
        elif volume_ratio > 10 and price_change > 3:
            flow_type = "heavy_outflow"
            score = 80
            net_flow = -volume_24h * 0.3
        elif volume_ratio > 5 and price_change < 0:
            flow_type = "moderate_inflow"
            score = 40
            net_flow = volume_24h * 0.15
        elif volume_ratio > 5 and price_change > 0:
            flow_type = "moderate_outflow"
            score = 65
            net_flow = -volume_24h * 0.15
        else:
            flow_type = "balanced"
            score = 50
            net_flow = 0
        
        return {
            "score": score,
            "flow_type": flow_type,
            "net_flow_estimate_usd": round(net_flow, 0),
        }


class OpenInterestProvider:
    async def get_open_interest(self, symbol: str, price_data: Dict) -> Dict[str, Any]:
        price_change_24h = price_data.get("price_change_24h", 0) or 0
        volume_24h = price_data.get("volume_24h", 0) or 0
        market_cap = price_data.get("market_cap", 1) or 1
        volume_ratio = (volume_24h / market_cap) * 100 if market_cap > 0 else 0
        
        if volume_ratio > 8 and price_change_24h > 2:
            oi_change = "increasing"
            oi_signal = "new_longs"
            score = 70
        elif volume_ratio > 8 and price_change_24h < -2:
            oi_change = "increasing"
            oi_signal = "new_shorts"
            score = 35
        else:
            oi_change = "stable"
            oi_signal = "neutral"
            score = 50
        
        return {
            "score": score,
            "oi_change": oi_change,
            "signal": oi_signal,
        }


class SocialSentimentProvider:
    async def get_social_sentiment(self, symbol: str, price_data: Dict) -> Dict[str, Any]:
        sentiment_up = price_data.get("sentiment_votes_up", 50) or 50
        sentiment_down = price_data.get("sentiment_votes_down", 50) or 50
        twitter_followers = price_data.get("twitter_followers", 0) or 0
        reddit_subscribers = price_data.get("reddit_subscribers", 0) or 0
        
        total_votes = sentiment_up + sentiment_down
        bullish_ratio = sentiment_up / total_votes if total_votes > 0 else 0.5
        sentiment_score = int(bullish_ratio * 100)
        
        if sentiment_score >= 80:
            sentiment_level = "extreme_bullish"
            oracle_score = 40
        elif sentiment_score >= 65:
            sentiment_level = "bullish"
            oracle_score = 55
        elif sentiment_score >= 45:
            sentiment_level = "neutral"
            oracle_score = 50
        elif sentiment_score >= 30:
            sentiment_level = "bearish"
            oracle_score = 60
        else:
            sentiment_level = "extreme_bearish"
            oracle_score = 75
        
        return {
            "score": oracle_score,
            "sentiment_score": sentiment_score,
            "sentiment_level": sentiment_level,
            "bullish_votes_pct": round(bullish_ratio * 100, 1),
            "twitter_followers": twitter_followers,
            "reddit_subscribers": reddit_subscribers,
        }


coingecko = CoinGeckoProvider()
fear_greed = FearGreedProvider()
whale_alert = WhaleAlertProvider()
liquidation = LiquidationProvider()
funding_rate = FundingRateProvider()
exchange_flow = ExchangeFlowProvider()
open_interest = OpenInterestProvider()
social_sentiment = SocialSentimentProvider()
