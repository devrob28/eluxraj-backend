"""
Enhanced Data Providers for ORACLE
Real data sources for whale alerts, liquidations, funding rates, etc.
"""
import httpx
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from app.core.logging import logger

# ============================================================================
# COINGECKO - Price & Market Data (existing, enhanced)
# ============================================================================

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
        """Get comprehensive price data for a symbol"""
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
                    # Community data for social sentiment
                    "twitter_followers": data.get("community_data", {}).get("twitter_followers"),
                    "reddit_subscribers": data.get("community_data", {}).get("reddit_subscribers"),
                    "sentiment_votes_up": data.get("sentiment_votes_up_percentage"),
                    "sentiment_votes_down": data.get("sentiment_votes_down_percentage"),
                }
                
        except Exception as e:
            logger.error(f"CoinGecko fetch error: {e}")
            return None
    
    async def get_market_chart(self, symbol: str, days: int = 7) -> Optional[Dict[str, Any]]:
        """Get historical price data"""
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


# ============================================================================
# FEAR & GREED INDEX
# ============================================================================

class FearGreedProvider:
    BASE_URL = "https://api.alternative.me/fng/"
    
    async def get_current(self) -> Optional[Dict[str, Any]]:
        """Get current Fear & Greed index"""
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
    
    async def get_historical(self, days: int = 30) -> Optional[List[Dict[str, Any]]]:
        """Get historical Fear & Greed data"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(self.BASE_URL, params={"limit": days})
                
                if response.status_code != 200:
                    return None
                
                data = response.json()
                return data.get("data", [])
                
        except Exception as e:
            logger.error(f"Fear & Greed historical error: {e}")
            return None


# ============================================================================
# WHALE ALERT - Large Transaction Monitoring
# ============================================================================

class WhaleAlertProvider:
    """
    Monitors large transactions using blockchain APIs
    Free tier: Uses CoinGecko volume spikes as proxy
    """
    
    # Whale thresholds (in USD)
    WHALE_THRESHOLD = {
        "BTC": 10_000_000,   # $10M+
        "ETH": 5_000_000,    # $5M+
        "SOL": 2_000_000,    # $2M+
        "default": 1_000_000  # $1M+
    }
    
    async def get_whale_activity(self, symbol: str, price_data: Dict) -> Dict[str, Any]:
        """
        Analyze whale activity based on volume patterns
        Returns whale score and recent alerts
        """
        volume_24h = price_data.get("volume_24h", 0) or 0
        market_cap = price_data.get("market_cap", 1) or 1
        price_change = price_data.get("price_change_24h", 0) or 0
        
        # Volume to market cap ratio (higher = more whale activity)
        volume_ratio = (volume_24h / market_cap) * 100 if market_cap > 0 else 0
        
        # Calculate whale score
        whale_score = 50  # neutral baseline
        whale_signals = []
        activity_type = "neutral"
        
        # High volume + price up = accumulation
        if volume_ratio > 15 and price_change > 2:
            whale_score = 85
            activity_type = "heavy_accumulation"
            whale_signals.append({
                "type": "accumulation",
                "title": "🐋 Whale Accumulation Detected",
                "description": f"Volume surge {volume_ratio:.1f}% of market cap with +{price_change:.1f}% price",
                "impact": "bullish",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # High volume + price down = distribution
        elif volume_ratio > 15 and price_change < -2:
            whale_score = 25
            activity_type = "heavy_distribution"
            whale_signals.append({
                "type": "distribution",
                "title": "🐋 Whale Distribution Alert",
                "description": f"Volume surge {volume_ratio:.1f}% of market cap with {price_change:.1f}% price drop",
                "impact": "bearish",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Moderate volume + price up = accumulation
        elif volume_ratio > 8 and price_change > 1:
            whale_score = 70
            activity_type = "accumulating"
            whale_signals.append({
                "type": "accumulation",
                "title": "🐋 Whale Activity",
                "description": "Above average volume with bullish price action",
                "impact": "bullish",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Moderate volume + price down = distribution
        elif volume_ratio > 8 and price_change < -1:
            whale_score = 35
            activity_type = "distributing"
            whale_signals.append({
                "type": "distribution",
                "title": "🐋 Whale Selling",
                "description": "Above average volume with bearish price action",
                "impact": "bearish",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Low volume = whales waiting
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


# ============================================================================
# LIQUIDATION HEATMAP - Leverage Positions at Risk
# ============================================================================

class LiquidationProvider:
    """
    Estimates liquidation zones based on market data
    Uses price levels and volatility to estimate where liquidations cluster
    """
    
    async def get_liquidation_data(self, symbol: str, price_data: Dict, chart_data: Dict) -> Dict[str, Any]:
        """
        Calculate liquidation heatmap data
        """
        current_price = price_data.get("current_price", 0)
        high_24h = price_data.get("high_24h", 0) or current_price
        low_24h = price_data.get("low_24h", 0) or current_price
        
        if not current_price:
            return {"score": 50, "risk_level": "unknown", "zones": []}
        
        # Calculate key liquidation zones
        # Long liquidations cluster below support levels
        # Short liquidations cluster above resistance levels
        
        price_range = high_24h - low_24h
        volatility_pct = (price_range / current_price) * 100 if current_price else 0
        
        # Estimate liquidation zones
        zones = []
        
        # Long liquidation zone (below current price)
        long_liq_1 = current_price * 0.95  # -5% 
        long_liq_2 = current_price * 0.90  # -10%
        long_liq_3 = current_price * 0.85  # -15%
        
        # Short liquidation zone (above current price)
        short_liq_1 = current_price * 1.05  # +5%
        short_liq_2 = current_price * 1.10  # +10%
        short_liq_3 = current_price * 1.15  # +15%
        
        zones = [
            {"type": "long", "price": round(long_liq_1, 2), "intensity": "high", "leverage": "10x"},
            {"type": "long", "price": round(long_liq_2, 2), "intensity": "medium", "leverage": "5x"},
            {"type": "long", "price": round(long_liq_3, 2), "intensity": "low", "leverage": "3x"},
            {"type": "short", "price": round(short_liq_1, 2), "intensity": "high", "leverage": "10x"},
            {"type": "short", "price": round(short_liq_2, 2), "intensity": "medium", "leverage": "5x"},
            {"type": "short", "price": round(short_liq_3, 2), "intensity": "low", "leverage": "3x"},
        ]
        
        # Calculate liquidation risk score
        # Higher volatility = higher liquidation risk
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
        
        # Estimate total liquidations in 24h (simulated based on volatility)
        estimated_liq_usd = volatility_pct * 50_000_000  # Rough estimate
        
        return {
            "score": risk_score,
            "risk_level": risk_level,
            "volatility_24h": round(volatility_pct, 2),
            "zones": zones,
            "estimated_liquidations_24h": round(estimated_liq_usd, 0),
            "nearest_long_liq": round(long_liq_1, 2),
            "nearest_short_liq": round(short_liq_1, 2),
            "distance_to_long_liq_pct": round(((current_price - long_liq_1) / current_price) * 100, 2),
            "distance_to_short_liq_pct": round(((short_liq_1 - current_price) / current_price) * 100, 2),
        }


# ============================================================================
# FUNDING RATE - Long/Short Sentiment
# ============================================================================

class FundingRateProvider:
    """
    Funding rates indicate whether longs or shorts are dominant
    Positive = longs pay shorts (bullish sentiment)
    Negative = shorts pay longs (bearish sentiment)
    """
    
    # Historical average funding rates for estimation
    BASELINE_FUNDING = 0.01  # 0.01% per 8h is neutral
    
    async def get_funding_data(self, symbol: str, price_data: Dict) -> Dict[str, Any]:
        """
        Estimate funding rate sentiment based on price action
        In production, use Binance/Bybit API for real funding rates
        """
        price_change_24h = price_data.get("price_change_24h", 0) or 0
        price_change_7d = price_data.get("price_change_7d", 0) or 0
        
        # Estimate funding rate based on price momentum
        # Strong uptrend = positive funding (longs pay)
        # Strong downtrend = negative funding (shorts pay)
        
        if price_change_24h > 5:
            estimated_funding = 0.05 + (price_change_24h - 5) * 0.01
            sentiment = "extreme_long"
            score = 30  # Contrarian: too many longs = bearish signal
        elif price_change_24h > 2:
            estimated_funding = 0.02 + (price_change_24h - 2) * 0.01
            sentiment = "long_heavy"
            score = 45
        elif price_change_24h > -2:
            estimated_funding = 0.01
            sentiment = "balanced"
            score = 60
        elif price_change_24h > -5:
            estimated_funding = -0.02 + (price_change_24h + 2) * 0.01
            sentiment = "short_heavy"
            score = 70  # Contrarian: shorts getting squeezed
        else:
            estimated_funding = -0.05 + (price_change_24h + 5) * 0.01
            sentiment = "extreme_short"
            score = 80  # Contrarian: extreme shorts = bullish
        
        # Calculate annualized funding rate
        annualized = estimated_funding * 3 * 365  # 3 funding periods per day
        
        return {
            "score": score,
            "estimated_funding_8h": round(estimated_funding, 4),
            "annualized_rate": round(annualized, 2),
            "sentiment": sentiment,
            "long_short_ratio": self._estimate_long_short_ratio(estimated_funding),
            "interpretation": self._get_interpretation(sentiment),
        }
    
    def _estimate_long_short_ratio(self, funding: float) -> float:
        """Estimate long/short ratio from funding rate"""
        if funding > 0.03:
            return 1.5  # 60% long, 40% short
        elif funding > 0.01:
            return 1.2  # 55% long, 45% short
        elif funding > -0.01:
            return 1.0  # 50/50
        elif funding > -0.03:
            return 0.8  # 45% long, 55% short
        else:
            return 0.6  # 40% long, 60% short
    
    def _get_interpretation(self, sentiment: str) -> str:
        interpretations = {
            "extreme_long": "Market heavily long - potential for long squeeze",
            "long_heavy": "More longs than shorts - mild bearish signal",
            "balanced": "Market balanced - neutral outlook",
            "short_heavy": "More shorts than longs - potential short squeeze",
            "extreme_short": "Market heavily short - high squeeze potential",
        }
        return interpretations.get(sentiment, "Unknown")


# ============================================================================
# EXCHANGE FLOW - Smart Money Movement
# ============================================================================

class ExchangeFlowProvider:
    """
    Track exchange inflows/outflows
    Inflows = potential selling pressure
    Outflows = accumulation (bullish)
    """
    
    async def get_exchange_flow(self, symbol: str, price_data: Dict) -> Dict[str, Any]:
        """
        Estimate exchange flow based on volume and price patterns
        In production, use Glassnode or CryptoQuant APIs
        """
        volume_24h = price_data.get("volume_24h", 0) or 0
        market_cap = price_data.get("market_cap", 1) or 1
        price_change = price_data.get("price_change_24h", 0) or 0
        
        volume_ratio = (volume_24h / market_cap) * 100 if market_cap > 0 else 0
        
        # High volume + price drop = exchange inflows (selling)
        # High volume + price up = exchange outflows (buying)
        
        if volume_ratio > 10 and price_change < -3:
            flow_type = "heavy_inflow"
            score = 25
            net_flow_estimate = volume_24h * 0.3  # 30% estimated as exchange inflow
        elif volume_ratio > 10 and price_change > 3:
            flow_type = "heavy_outflow"
            score = 80
            net_flow_estimate = -volume_24h * 0.3  # Negative = outflow
        elif volume_ratio > 5 and price_change < 0:
            flow_type = "moderate_inflow"
            score = 40
            net_flow_estimate = volume_24h * 0.15
        elif volume_ratio > 5 and price_change > 0:
            flow_type = "moderate_outflow"
            score = 65
            net_flow_estimate = -volume_24h * 0.15
        else:
            flow_type = "balanced"
            score = 50
            net_flow_estimate = 0
        
        return {
            "score": score,
            "flow_type": flow_type,
            "net_flow_estimate_usd": round(net_flow_estimate, 0),
            "interpretation": self._get_interpretation(flow_type),
            "signal": "bullish" if score > 55 else "bearish" if score < 45 else "neutral",
        }
    
    def _get_interpretation(self, flow_type: str) -> str:
        interpretations = {
            "heavy_inflow": "Large amounts moving to exchanges - selling pressure likely",
            "moderate_inflow": "Above average exchange deposits - mild bearish",
            "balanced": "Normal exchange activity",
            "moderate_outflow": "Coins leaving exchanges - accumulation signal",
            "heavy_outflow": "Strong outflows from exchanges - bullish accumulation",
        }
        return interpretations.get(flow_type, "Unknown")


# ============================================================================
# OPEN INTEREST - Derivatives Market Positioning
# ============================================================================

class OpenInterestProvider:
    """
    Track open interest in derivatives markets
    Rising OI + rising price = new longs (bullish)
    Rising OI + falling price = new shorts (bearish)
    """
    
    async def get_open_interest(self, symbol: str, price_data: Dict) -> Dict[str, Any]:
        """
        Estimate open interest dynamics
        In production, use Coinalyze or exchange APIs
        """
        price_change_24h = price_data.get("price_change_24h", 0) or 0
        volume_24h = price_data.get("volume_24h", 0) or 0
        
        # Estimate OI change based on volume (proxy)
        # High volume typically correlates with OI changes
        market_cap = price_data.get("market_cap", 1) or 1
        volume_ratio = (volume_24h / market_cap) * 100 if market_cap > 0 else 0
        
        # Estimate OI change direction
        if volume_ratio > 8 and price_change_24h > 2:
            oi_change = "increasing"
            oi_signal = "new_longs"
            score = 70
        elif volume_ratio > 8 and price_change_24h < -2:
            oi_change = "increasing"
            oi_signal = "new_shorts"
            score = 35
        elif volume_ratio < 4 and abs(price_change_24h) > 3:
            oi_change = "decreasing"
            oi_signal = "position_closing"
            score = 50
        else:
            oi_change = "stable"
            oi_signal = "neutral"
            score = 50
        
        return {
            "score": score,
            "oi_change": oi_change,
            "signal": oi_signal,
            "interpretation": self._get_interpretation(oi_signal),
            "estimated_oi_change_pct": round(volume_ratio * 0.5, 2),  # Rough estimate
        }
    
    def _get_interpretation(self, signal: str) -> str:
        interpretations = {
            "new_longs": "New long positions opening - bullish momentum",
            "new_shorts": "New short positions opening - bearish pressure",
            "position_closing": "Positions being closed - trend exhaustion",
            "neutral": "Stable open interest",
        }
        return interpretations.get(signal, "Unknown")


# ============================================================================
# SOCIAL SENTIMENT - Twitter/Reddit Analysis
# ============================================================================

class SocialSentimentProvider:
    """
    Analyze social sentiment from CoinGecko community data
    """
    
    async def get_social_sentiment(self, symbol: str, price_data: Dict) -> Dict[str, Any]:
        """
        Analyze social sentiment
        """
        sentiment_up = price_data.get("sentiment_votes_up", 50) or 50
        sentiment_down = price_data.get("sentiment_votes_down", 50) or 50
        twitter_followers = price_data.get("twitter_followers", 0) or 0
        reddit_subscribers = price_data.get("reddit_subscribers", 0) or 0
        
        # Calculate sentiment score
        total_votes = sentiment_up + sentiment_down
        if total_votes > 0:
            bullish_ratio = sentiment_up / total_votes
        else:
            bullish_ratio = 0.5
        
        # Convert to score (0-100)
        sentiment_score = int(bullish_ratio * 100)
        
        # Determine sentiment level
        if sentiment_score >= 80:
            sentiment_level = "extreme_bullish"
            oracle_score = 40  # Contrarian
        elif sentiment_score >= 65:
            sentiment_level = "bullish"
            oracle_score = 55
        elif sentiment_score >= 45:
            sentiment_level = "neutral"
            oracle_score = 50
        elif sentiment_score >= 30:
            sentiment_level = "bearish"
            oracle_score = 60  # Contrarian
        else:
            sentiment_level = "extreme_bearish"
            oracle_score = 75  # Contrarian
        
        return {
            "score": oracle_score,
            "sentiment_score": sentiment_score,
            "sentiment_level": sentiment_level,
            "bullish_votes_pct": round(bullish_ratio * 100, 1),
            "twitter_followers": twitter_followers,
            "reddit_subscribers": reddit_subscribers,
            "social_volume": self._categorize_social_volume(twitter_followers, reddit_subscribers),
        }
    
    def _categorize_social_volume(self, twitter: int, reddit: int) -> str:
        total = twitter + reddit
        if total > 5_000_000:
            return "massive"
        elif total > 1_000_000:
            return "high"
        elif total > 100_000:
            return "moderate"
        else:
            return "low"


# ============================================================================
# Initialize providers
# ============================================================================

coingecko = CoinGeckoProvider()
fear_greed = FearGreedProvider()
whale_alert = WhaleAlertProvider()
liquidation = LiquidationProvider()
funding_rate = FundingRateProvider()
exchange_flow = ExchangeFlowProvider()
open_interest = OpenInterestProvider()
social_sentiment = SocialSentimentProvider()
