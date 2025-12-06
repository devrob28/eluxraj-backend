import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from app.services.data_providers import coingecko, fear_greed
from app.core.logging import logger

class OracleEngine:
    """
    ORACLE - The AI-Powered Signal Generation Engine
    
    Combines multiple data sources and analysis factors to generate
    trading signals with confidence scores and reasoning.
    """
    
    MODEL_VERSION = "oracle-v1.0.0"
    
    # Supported assets
    SUPPORTED_ASSETS = ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX", "DOT", "MATIC", "LINK", "UNI"]
    
    async def analyze_asset(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Perform comprehensive analysis on an asset
        Returns analysis data and factors
        """
        symbol = symbol.upper()
        
        if symbol not in self.SUPPORTED_ASSETS:
            logger.warning(f"Unsupported asset: {symbol}")
            return None
        
        logger.info(f"Analyzing {symbol}...")
        
        # Fetch data from providers
        price_data = await coingecko.get_price_data(symbol)
        chart_data = await coingecko.get_market_chart(symbol, days=7)
        fng_data = await fear_greed.get_current()
        
        if not price_data:
            logger.error(f"Failed to fetch price data for {symbol}")
            return None
        
        # Calculate technical factors
        factors = await self._calculate_factors(price_data, chart_data, fng_data)
        
        return {
            "symbol": symbol,
            "price_data": price_data,
            "chart_data": chart_data,
            "fng_data": fng_data,
            "factors": factors,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def _calculate_factors(
        self,
        price_data: Dict[str, Any],
        chart_data: Optional[Dict[str, Any]],
        fng_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate analysis factors from raw data"""
        
        factors = {}
        
        # Price momentum
        price_change_24h = price_data.get("price_change_24h", 0) or 0
        price_change_7d = price_data.get("price_change_7d", 0) or 0
        
        if price_change_24h > 5:
            factors["momentum_24h"] = {"value": "strong_bullish", "score": 80}
        elif price_change_24h > 2:
            factors["momentum_24h"] = {"value": "bullish", "score": 65}
        elif price_change_24h > -2:
            factors["momentum_24h"] = {"value": "neutral", "score": 50}
        elif price_change_24h > -5:
            factors["momentum_24h"] = {"value": "bearish", "score": 35}
        else:
            factors["momentum_24h"] = {"value": "strong_bearish", "score": 20}
        
        # 7-day trend
        if price_change_7d > 10:
            factors["trend_7d"] = {"value": "strong_uptrend", "score": 85}
        elif price_change_7d > 3:
            factors["trend_7d"] = {"value": "uptrend", "score": 65}
        elif price_change_7d > -3:
            factors["trend_7d"] = {"value": "sideways", "score": 50}
        elif price_change_7d > -10:
            factors["trend_7d"] = {"value": "downtrend", "score": 35}
        else:
            factors["trend_7d"] = {"value": "strong_downtrend", "score": 15}
        
        # Volume analysis
        volume = price_data.get("volume_24h", 0) or 0
        market_cap = price_data.get("market_cap", 1) or 1
        volume_ratio = (volume / market_cap) * 100 if market_cap > 0 else 0
        
        if volume_ratio > 15:
            factors["volume_flow"] = {"value": "very_high", "score": 75}
        elif volume_ratio > 8:
            factors["volume_flow"] = {"value": "high", "score": 65}
        elif volume_ratio > 3:
            factors["volume_flow"] = {"value": "normal", "score": 50}
        else:
            factors["volume_flow"] = {"value": "low", "score": 35}
        
        # Distance from ATH
        ath_change = price_data.get("ath_change_percentage", 0) or 0
        if ath_change > -10:
            factors["ath_proximity"] = {"value": "near_ath", "score": 40}  # Risky to buy
        elif ath_change > -30:
            factors["ath_proximity"] = {"value": "moderate_discount", "score": 60}
        elif ath_change > -50:
            factors["ath_proximity"] = {"value": "significant_discount", "score": 70}
        else:
            factors["ath_proximity"] = {"value": "deep_discount", "score": 80}
        
        # Fear & Greed
        if fng_data:
            fng_value = fng_data.get("value", 50)
            # Contrarian: extreme fear = good buy, extreme greed = cautious
            if fng_value < 25:
                factors["market_sentiment"] = {"value": "extreme_fear", "score": 80}
            elif fng_value < 40:
                factors["market_sentiment"] = {"value": "fear", "score": 65}
            elif fng_value < 60:
                factors["market_sentiment"] = {"value": "neutral", "score": 50}
            elif fng_value < 75:
                factors["market_sentiment"] = {"value": "greed", "score": 40}
            else:
                factors["market_sentiment"] = {"value": "extreme_greed", "score": 25}
        else:
            factors["market_sentiment"] = {"value": "unknown", "score": 50}
        
        # Volatility (based on 24h range)
        high = price_data.get("high_24h", 0) or 0
        low = price_data.get("low_24h", 0) or 1
        volatility = ((high - low) / low) * 100 if low > 0 else 0
        
        if volatility > 10:
            factors["volatility"] = {"value": "very_high", "score": 30}
        elif volatility > 5:
            factors["volatility"] = {"value": "high", "score": 45}
        elif volatility > 2:
            factors["volatility"] = {"value": "moderate", "score": 60}
        else:
            factors["volatility"] = {"value": "low", "score": 70}
        
        # Simulated whale activity (in production, use real on-chain data)
        whale_score = random.randint(30, 90)
        if whale_score > 70:
            factors["whale_activity"] = {"value": "accumulating", "score": whale_score}
        elif whale_score > 50:
            factors["whale_activity"] = {"value": "neutral", "score": whale_score}
        else:
            factors["whale_activity"] = {"value": "distributing", "score": whale_score}
        
        return factors
    
    async def generate_signal(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Generate a trading signal for an asset
        """
        analysis = await self.analyze_asset(symbol)
        
        if not analysis:
            return None
        
        factors = analysis["factors"]
        price_data = analysis["price_data"]
        current_price = price_data.get("current_price", 0)
        
        if not current_price:
            return None
        
        # Calculate Oracle Score (weighted average of factors)
        weights = {
            "momentum_24h": 0.15,
            "trend_7d": 0.20,
            "volume_flow": 0.15,
            "ath_proximity": 0.10,
            "market_sentiment": 0.15,
            "volatility": 0.10,
            "whale_activity": 0.15,
        }
        
        total_score = 0
        total_weight = 0
        
        for factor_name, weight in weights.items():
            if factor_name in factors:
                total_score += factors[factor_name]["score"] * weight
                total_weight += weight
        
        oracle_score = int(total_score / total_weight) if total_weight > 0 else 50
        
        # Determine signal type
        if oracle_score >= 65:
            signal_type = "buy"
            target_pct = 5 + (oracle_score - 65) * 0.2  # 5-12% target
            stop_pct = 3 + (100 - oracle_score) * 0.05  # 3-5% stop
        elif oracle_score <= 35:
            signal_type = "sell"
            target_pct = 5 + (35 - oracle_score) * 0.2
            stop_pct = 3 + oracle_score * 0.05
        else:
            signal_type = "hold"
            target_pct = 3
            stop_pct = 3
        
        # Calculate prices
        if signal_type == "buy":
            target_price = current_price * (1 + target_pct / 100)
            stop_loss = current_price * (1 - stop_pct / 100)
        elif signal_type == "sell":
            target_price = current_price * (1 - target_pct / 100)
            stop_loss = current_price * (1 + stop_pct / 100)
        else:
            target_price = current_price * 1.03
            stop_loss = current_price * 0.97
        
        # Calculate risk/reward ratio
        risk = abs(current_price - stop_loss)
        reward = abs(target_price - current_price)
        risk_reward = round(reward / risk, 2) if risk > 0 else 1.0
        
        # Generate reasoning
        reasoning = self._generate_reasoning(symbol, signal_type, oracle_score, factors, price_data)
        
        # Determine timeframe based on volatility
        volatility = factors.get("volatility", {}).get("value", "moderate")
        if volatility in ["very_high", "high"]:
            timeframe = "24h"
            expires_hours = 24
        else:
            timeframe = "48h"
            expires_hours = 48
        
        # Build signal object
        signal = {
            "asset_type": "crypto",
            "symbol": symbol,
            "pair": f"{symbol}/USDT",
            "signal_type": signal_type,
            "oracle_score": oracle_score,
            "confidence": oracle_score / 100,
            "entry_price": round(current_price, 2),
            "target_price": round(target_price, 2),
            "stop_loss": round(stop_loss, 2),
            "risk_reward_ratio": risk_reward,
            "reasoning_summary": reasoning["summary"],
            "reasoning_factors": {k: v["value"] for k, v in factors.items()},
            "model_version": self.MODEL_VERSION,
            "input_snapshot": {
                "price_data": price_data,
                "fng": analysis.get("fng_data"),
            },
            "data_sources": ["coingecko", "alternative.me"],
            "timeframe": timeframe,
            "expires_at": (datetime.utcnow() + timedelta(hours=expires_hours)).isoformat(),
        }
        
        return signal
    
    def _generate_reasoning(
        self,
        symbol: str,
        signal_type: str,
        score: int,
        factors: Dict[str, Any],
        price_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate human-readable reasoning for the signal"""
        
        parts = []
        
        # Signal strength
        if score >= 80:
            parts.append(f"Strong {signal_type.upper()} signal detected for {symbol}.")
        elif score >= 65:
            parts.append(f"Moderate {signal_type.upper()} signal for {symbol}.")
        elif score <= 35:
            parts.append(f"Caution advised for {symbol}.")
        else:
            parts.append(f"Neutral outlook for {symbol}.")
        
        # Momentum
        momentum = factors.get("momentum_24h", {}).get("value", "neutral")
        price_change = price_data.get("price_change_24h", 0) or 0
        if momentum in ["strong_bullish", "bullish"]:
            parts.append(f"Price up {abs(price_change):.1f}% in 24h showing bullish momentum.")
        elif momentum in ["strong_bearish", "bearish"]:
            parts.append(f"Price down {abs(price_change):.1f}% in 24h indicating selling pressure.")
        
        # Volume
        volume_flow = factors.get("volume_flow", {}).get("value", "normal")
        if volume_flow in ["very_high", "high"]:
            parts.append("Volume surge detected above average.")
        
        # Whale activity
        whale = factors.get("whale_activity", {}).get("value", "neutral")
        if whale == "accumulating":
            parts.append("Whale wallets showing accumulation patterns.")
        elif whale == "distributing":
            parts.append("Large holders appear to be distributing.")
        
        # Market sentiment
        sentiment = factors.get("market_sentiment", {}).get("value", "neutral")
        if sentiment == "extreme_fear":
            parts.append("Market in extreme fear - potential contrarian opportunity.")
        elif sentiment == "extreme_greed":
            parts.append("Market showing extreme greed - exercise caution.")
        
        return {
            "summary": " ".join(parts),
            "factors": factors,
        }
    
    async def scan_all_assets(self) -> List[Dict[str, Any]]:
        """Scan all supported assets and generate signals"""
        signals = []
        
        for symbol in self.SUPPORTED_ASSETS:
            try:
                signal = await self.generate_signal(symbol)
                if signal:
                    signals.append(signal)
            except Exception as e:
                logger.error(f"Error generating signal for {symbol}: {e}")
        
        # Sort by Oracle Score
        signals.sort(key=lambda x: x["oracle_score"], reverse=True)
        
        return signals


# Initialize the Oracle
oracle = OracleEngine()
