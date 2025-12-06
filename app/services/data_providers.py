import httpx
from typing import Dict, Any, Optional
from datetime import datetime
from app.core.logging import logger

class CoinGeckoProvider:
    """Fetch crypto market data from CoinGecko"""
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    COIN_IDS = {
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
    }
    
    async def get_price_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current price and market data"""
        coin_id = self.COIN_IDS.get(symbol.upper())
        if not coin_id:
            logger.warning(f"Unknown symbol: {symbol}")
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/coins/{coin_id}",
                    params={
                        "localization": "false",
                        "tickers": "false",
                        "community_data": "false",
                        "developer_data": "false"
                    },
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    logger.error(f"CoinGecko API error: {response.status_code}")
                    return None
                
                data = response.json()
                market_data = data.get("market_data", {})
                
                return {
                    "symbol": symbol.upper(),
                    "name": data.get("name"),
                    "current_price": market_data.get("current_price", {}).get("usd"),
                    "market_cap": market_data.get("market_cap", {}).get("usd"),
                    "volume_24h": market_data.get("total_volume", {}).get("usd"),
                    "price_change_24h": market_data.get("price_change_percentage_24h"),
                    "price_change_7d": market_data.get("price_change_percentage_7d"),
                    "price_change_30d": market_data.get("price_change_percentage_30d"),
                    "ath": market_data.get("ath", {}).get("usd"),
                    "ath_change_percentage": market_data.get("ath_change_percentage", {}).get("usd"),
                    "atl": market_data.get("atl", {}).get("usd"),
                    "high_24h": market_data.get("high_24h", {}).get("usd"),
                    "low_24h": market_data.get("low_24h", {}).get("usd"),
                    "circulating_supply": market_data.get("circulating_supply"),
                    "total_supply": market_data.get("total_supply"),
                    "last_updated": data.get("last_updated"),
                }
                
        except Exception as e:
            logger.error(f"Error fetching CoinGecko data: {e}")
            return None
    
    async def get_market_chart(self, symbol: str, days: int = 7) -> Optional[Dict[str, Any]]:
        """Get historical price data"""
        coin_id = self.COIN_IDS.get(symbol.upper())
        if not coin_id:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/coins/{coin_id}/market_chart",
                    params={"vs_currency": "usd", "days": days},
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    return None
                
                data = response.json()
                prices = data.get("prices", [])
                volumes = data.get("total_volumes", [])
                
                return {
                    "prices": prices,
                    "volumes": volumes,
                    "price_count": len(prices),
                }
                
        except Exception as e:
            logger.error(f"Error fetching market chart: {e}")
            return None


class FearGreedProvider:
    """Fetch Fear & Greed Index"""
    
    BASE_URL = "https://api.alternative.me/fng/"
    
    async def get_current(self) -> Optional[Dict[str, Any]]:
        """Get current Fear & Greed Index"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.BASE_URL,
                    params={"limit": 1},
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    return None
                
                data = response.json()
                if data.get("data"):
                    fng = data["data"][0]
                    return {
                        "value": int(fng.get("value", 50)),
                        "classification": fng.get("value_classification", "Neutral"),
                        "timestamp": fng.get("timestamp"),
                    }
                return None
                
        except Exception as e:
            logger.error(f"Error fetching Fear & Greed: {e}")
            return None
    
    async def get_history(self, days: int = 30) -> Optional[list]:
        """Get historical Fear & Greed data"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.BASE_URL,
                    params={"limit": days},
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    return None
                
                data = response.json()
                return [
                    {
                        "value": int(item.get("value", 50)),
                        "classification": item.get("value_classification"),
                        "timestamp": item.get("timestamp"),
                    }
                    for item in data.get("data", [])
                ]
                
        except Exception as e:
            logger.error(f"Error fetching Fear & Greed history: {e}")
            return None


# Initialize providers
coingecko = CoinGeckoProvider()
fear_greed = FearGreedProvider()
