"""
Enhanced Data Providers for ORACLE v2.0 with Caching
"""
import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.logging import logger

# Simple in-memory cache
_cache = {}
CACHE_TTL = 60  # Cache for 60 seconds


def get_cached(key: str) -> Optional[Dict]:
    if key in _cache:
        data, timestamp = _cache[key]
        if datetime.utcnow() - timestamp < timedelta(seconds=CACHE_TTL):
            return data
    return None


def set_cached(key: str, data: Dict):
    _cache[key] = (data, datetime.utcnow())


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
    }
    
    async def get_price_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        coin_id = self.SYMBOL_MAP.get(symbol.upper())
        if not coin_id:
            return None
        
        # Check cache first
        cache_key = f"price_{symbol.upper()}"
        cached = get_cached(cache_key)
        if cached:
            logger.info(f"Using cached data for {symbol}")
            return cached
        
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(
                    f"{self.BASE_URL}/coins/{coin_id}",
                    params={
                        "localization": "false",
                        "tickers": "false",
                        "market_data": "true",
                        "community_data": "true",
                        "developer_data": "false",
                    },
                    headers={"Accept": "application/json"}
                )
                
                if response.status_code == 429:
                    logger.warning(f"CoinGecko rate limited, using fallback for {symbol}")
                    return await self._get_simple_price(symbol)
                
                if response.status_code != 200:
                    logger.error(f"CoinGecko error: {response.status_code}")
                    return await self._get_simple_price(symbol)
                
                data = response.json()
                market = data.get("market_data", {})
                
                result = {
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
                
                set_cached(cache_key, result)
                return result
                
        except Exception as e:
            logger.error(f"CoinGecko fetch error: {e}")
            return await self._get_simple_price(symbol)
    
    async def _get_simple_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fallback to simple price API which has higher rate limits"""
        coin_id = self.SYMBOL_MAP.get(symbol.upper())
        if not coin_id:
            return None
            
        cache_key = f"simple_{symbol.upper()}"
        cached = get_cached(cache_key)
        if cached:
            return cached
            
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.BASE_URL}/simple/price",
                    params={
                        "ids": coin_id,
                        "vs_currencies": "usd",
                        "include_24hr_change": "true",
                        "include_24hr_vol": "true",
                        "include_market_cap": "true",
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Simple price API error: {response.status_code}")
                    return None
                
                data = response.json().get(coin_id, {})
                
                result = {
                    "symbol": symbol.upper(),
                    "current_price": data.get("usd"),
                    "market_cap": data.get("usd_market_cap"),
                    "volume_24h": data.get("usd_24h_vol"),
                    "price_change_24h": data.get("usd_24h_change"),
                    "price_change_7d": None,
                    "price_change_30d": None,
                    "high_24h": data.get("usd", 0) * 1.02 if data.get("usd") else None,
                    "low_24h": data.get("usd", 0) * 0.98 if data.get("usd") else None,
                    "ath": None,
                    "ath_change_percentage": None,
                    "circulating_supply": None,
                    "total_supply": None,
                    "twitter_followers": None,
                    "reddit_subscribers": None,
                    "sentiment_votes_up": 50,
                    "sentiment_votes_down": 50,
                }
                
                set_cached(cache_key, result)
                return result
                
        except Exception as e:
            logger.error(f"Simple price fetch error: {e}")
            return None
    
    async def get_market_chart(self, symbol: str, days: int = 7) -> Optional[Dict[str, Any]]:
        coin_id = self.SYMBOL_MAP.get(symbol.upper())
        if not coin_id:
            return None
        
        cache_key = f"chart_{symbol.upper()}_{days}"
        cached = get_cached(cache_key)
        if cached:
            return cached
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.BASE_URL}/coins/{coin_id}/market_chart",
                    params={"vs_currency": "usd", "days": days}
                )
                
                if response.status_code != 200:
                    return None
                
                result = response.json()
                set_cached(cache_key, result)
                return result
                
        except Exception as e:
            logger.error(f"CoinGecko chart error: {e}")
            return None


class FearGreedProvider:
    BASE_URL = "https://api.alternative.me/fng/"
    
    async def get_current(self) -> Optional[Dict[str, Any]]:
        cache_key = "fear_greed"
        cached = get_cached(cache_key)
        if cached:
            return cached
            
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(self.BASE_URL, params={"limit": 1})
                
                if response.status_code != 200:
                    return {"value": 50, "classification": "Neutral", "timestamp": None}
                
                data = response.json()
                if data.get("data"):
                    item = data["data"][0]
                    result = {
                        "value": int(item.get("value", 50)),
                        "classification": item.get("value_classification", "Neutral"),
                        "timestamp": item.get("timestamp"),
                    }
                    set_cached(cache_key, result)
                    return result
                return {"value": 50, "classification": "Neutral", "timestamp": None}
                
        except Exception as e:
            logger.error(f"Fear & Greed fetch error: {e}")
            return {"value": 50, "classification": "Neutral", "timestamp": None}


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
        elif volume_ratio > 8 and price_change < -1:
            whale_score = 35
            activity_type = "distributing"
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
            "sentiment": sentiment,
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
        elif volume_ratio > 10 and price_change > 3:
            flow_type = "heavy_outflow"
            score = 80
        elif volume_ratio > 5 and price_change < 0:
            flow_type = "moderate_inflow"
            score = 40
        elif volume_ratio > 5 and price_change > 0:
            flow_type = "moderate_outflow"
            score = 65
        else:
            flow_type = "balanced"
            score = 50
        
        return {"score": score, "flow_type": flow_type}


class OpenInterestProvider:
    async def get_open_interest(self, symbol: str, price_data: Dict) -> Dict[str, Any]:
        price_change_24h = price_data.get("price_change_24h", 0) or 0
        volume_24h = price_data.get("volume_24h", 0) or 0
        market_cap = price_data.get("market_cap", 1) or 1
        volume_ratio = (volume_24h / market_cap) * 100 if market_cap > 0 else 0
        
        if volume_ratio > 8 and price_change_24h > 2:
            oi_signal = "new_longs"
            score = 70
        elif volume_ratio > 8 and price_change_24h < -2:
            oi_signal = "new_shorts"
            score = 35
        else:
            oi_signal = "neutral"
            score = 50
        
        return {"score": score, "signal": oi_signal}


class SocialSentimentProvider:
    async def get_social_sentiment(self, symbol: str, price_data: Dict) -> Dict[str, Any]:
        sentiment_up = price_data.get("sentiment_votes_up", 50) or 50
        sentiment_down = price_data.get("sentiment_votes_down", 50) or 50
        
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
        
        return {"score": oracle_score, "sentiment_level": sentiment_level}


coingecko = CoinGeckoProvider()
fear_greed = FearGreedProvider()
whale_alert = WhaleAlertProvider()
liquidation = LiquidationProvider()
funding_rate = FundingRateProvider()
exchange_flow = ExchangeFlowProvider()
open_interest = OpenInterestProvider()
social_sentiment = SocialSentimentProvider()
