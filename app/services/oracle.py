"""
ORACLE v2.0 - Enhanced AI-Powered Signal Generation Engine
Elite-only feature ($98/mo)
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from app.services.data_providers import (
    coingecko, fear_greed, whale_alert, liquidation,
    funding_rate, exchange_flow, open_interest, social_sentiment,
)
from app.core.logging import logger


class OracleEngine:
    MODEL_VERSION = "oracle-v2.0.0"
    
    SUPPORTED_ASSETS = [
        "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", 
        "DOGE", "AVAX", "DOT", "MATIC", "LINK", "UNI",
        "PEPE", "SHIB"
    ]
    
    FACTOR_WEIGHTS = {
        "momentum_24h": 0.10,
        "trend_7d": 0.12,
        "volume_flow": 0.08,
        "ath_proximity": 0.05,
        "market_sentiment": 0.12,
        "volatility": 0.08,
        "whale_activity": 0.15,
        "liquidation_risk": 0.08,
        "funding_rate": 0.08,
        "exchange_flow": 0.07,
        "open_interest": 0.05,
        "social_sentiment": 0.02,
    }
    
    async def analyze_asset(self, symbol: str) -> Optional[Dict[str, Any]]:
        symbol = symbol.upper()
        
        if symbol not in self.SUPPORTED_ASSETS:
            logger.warning(f"Unsupported asset: {symbol}")
            return None
        
        logger.info(f"ORACLE analyzing {symbol}...")
        
        price_data = await coingecko.get_price_data(symbol)
        chart_data = await coingecko.get_market_chart(symbol, days=7)
        fng_data = await fear_greed.get_current()
        
        if not price_data:
            logger.error(f"Failed to fetch price data for {symbol}")
            return None
        
        whale_data = await whale_alert.get_whale_activity(symbol, price_data)
        liq_data = await liquidation.get_liquidation_data(symbol, price_data, chart_data or {})
        funding_data = await funding_rate.get_funding_data(symbol, price_data)
        flow_data = await exchange_flow.get_exchange_flow(symbol, price_data)
        oi_data = await open_interest.get_open_interest(symbol, price_data)
        social_data = await social_sentiment.get_social_sentiment(symbol, price_data)
        
        factors = await self._calculate_factors(
            price_data, chart_data, fng_data, whale_data, 
            liq_data, funding_data, flow_data, oi_data, social_data
        )
        
        return {
            "symbol": symbol,
            "price_data": price_data,
            "fng_data": fng_data,
            "whale_data": whale_data,
            "liquidation_data": liq_data,
            "funding_data": funding_data,
            "exchange_flow_data": flow_data,
            "open_interest_data": oi_data,
            "social_data": social_data,
            "factors": factors,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def _calculate_factors(self, price_data, chart_data, fng_data, whale_data, 
                                  liq_data, funding_data, flow_data, oi_data, social_data) -> Dict:
        factors = {}
        
        price_change_24h = price_data.get("price_change_24h", 0) or 0
        price_change_7d = price_data.get("price_change_7d", 0) or 0
        
        if price_change_24h > 5:
            factors["momentum_24h"] = {"value": "strong_bullish", "score": 80, "change": price_change_24h}
        elif price_change_24h > 2:
            factors["momentum_24h"] = {"value": "bullish", "score": 65, "change": price_change_24h}
        elif price_change_24h > -2:
            factors["momentum_24h"] = {"value": "neutral", "score": 50, "change": price_change_24h}
        elif price_change_24h > -5:
            factors["momentum_24h"] = {"value": "bearish", "score": 35, "change": price_change_24h}
        else:
            factors["momentum_24h"] = {"value": "strong_bearish", "score": 20, "change": price_change_24h}
        
        if price_change_7d > 10:
            factors["trend_7d"] = {"value": "strong_uptrend", "score": 85, "change": price_change_7d}
        elif price_change_7d > 3:
            factors["trend_7d"] = {"value": "uptrend", "score": 65, "change": price_change_7d}
        elif price_change_7d > -3:
            factors["trend_7d"] = {"value": "sideways", "score": 50, "change": price_change_7d}
        elif price_change_7d > -10:
            factors["trend_7d"] = {"value": "downtrend", "score": 35, "change": price_change_7d}
        else:
            factors["trend_7d"] = {"value": "strong_downtrend", "score": 15, "change": price_change_7d}
        
        volume = price_data.get("volume_24h", 0) or 0
        market_cap = price_data.get("market_cap", 1) or 1
        volume_ratio = (volume / market_cap) * 100 if market_cap > 0 else 0
        
        if volume_ratio > 15:
            factors["volume_flow"] = {"value": "very_high", "score": 75, "ratio": volume_ratio}
        elif volume_ratio > 8:
            factors["volume_flow"] = {"value": "high", "score": 65, "ratio": volume_ratio}
        elif volume_ratio > 3:
            factors["volume_flow"] = {"value": "normal", "score": 50, "ratio": volume_ratio}
        else:
            factors["volume_flow"] = {"value": "low", "score": 35, "ratio": volume_ratio}
        
        ath_change = price_data.get("ath_change_percentage", 0) or 0
        if ath_change > -10:
            factors["ath_proximity"] = {"value": "near_ath", "score": 40, "change": ath_change}
        elif ath_change > -30:
            factors["ath_proximity"] = {"value": "moderate_discount", "score": 60, "change": ath_change}
        elif ath_change > -50:
            factors["ath_proximity"] = {"value": "significant_discount", "score": 70, "change": ath_change}
        else:
            factors["ath_proximity"] = {"value": "deep_discount", "score": 80, "change": ath_change}
        
        high = price_data.get("high_24h", 0) or 0
        low = price_data.get("low_24h", 0) or 1
        volatility = ((high - low) / low) * 100 if low > 0 else 0
        
        if volatility > 10:
            factors["volatility"] = {"value": "very_high", "score": 30, "pct": volatility}
        elif volatility > 5:
            factors["volatility"] = {"value": "high", "score": 45, "pct": volatility}
        elif volatility > 2:
            factors["volatility"] = {"value": "moderate", "score": 60, "pct": volatility}
        else:
            factors["volatility"] = {"value": "low", "score": 70, "pct": volatility}
        
        if fng_data:
            fng_value = fng_data.get("value", 50)
            if fng_value < 25:
                factors["market_sentiment"] = {"value": "extreme_fear", "score": 80, "fng": fng_value}
            elif fng_value < 40:
                factors["market_sentiment"] = {"value": "fear", "score": 65, "fng": fng_value}
            elif fng_value < 60:
                factors["market_sentiment"] = {"value": "neutral", "score": 50, "fng": fng_value}
            elif fng_value < 75:
                factors["market_sentiment"] = {"value": "greed", "score": 40, "fng": fng_value}
            else:
                factors["market_sentiment"] = {"value": "extreme_greed", "score": 25, "fng": fng_value}
        else:
            factors["market_sentiment"] = {"value": "unknown", "score": 50, "fng": None}
        
        factors["whale_activity"] = {
            "value": whale_data.get("activity_type", "neutral"),
            "score": whale_data.get("score", 50),
            "signals": whale_data.get("signals", []),
        }
        
        factors["liquidation_risk"] = {
            "value": liq_data.get("risk_level", "moderate"),
            "score": 100 - liq_data.get("score", 50),
            "zones": liq_data.get("zones", []),
        }
        
        factors["funding_rate"] = {
            "value": funding_data.get("sentiment", "balanced"),
            "score": funding_data.get("score", 50),
            "rate_8h": funding_data.get("estimated_funding_8h", 0),
        }
        
        factors["exchange_flow"] = {
            "value": flow_data.get("flow_type", "balanced"),
            "score": flow_data.get("score", 50),
        }
        
        factors["open_interest"] = {
            "value": oi_data.get("signal", "neutral"),
            "score": oi_data.get("score", 50),
        }
        
        factors["social_sentiment"] = {
            "value": social_data.get("sentiment_level", "neutral"),
            "score": social_data.get("score", 50),
        }
        
        return factors
    
    async def generate_signal(self, symbol: str) -> Optional[Dict[str, Any]]:
        analysis = await self.analyze_asset(symbol)
        
        if not analysis:
            return None
        
        factors = analysis["factors"]
        price_data = analysis["price_data"]
        current_price = price_data.get("current_price", 0)
        
        if not current_price:
            return None
        
        total_score = 0
        total_weight = 0
        factor_breakdown = []
        
        for factor_name, weight in self.FACTOR_WEIGHTS.items():
            if factor_name in factors:
                score = factors[factor_name].get("score", 50)
                total_score += score * weight
                total_weight += weight
                factor_breakdown.append({
                    "name": factor_name,
                    "score": score,
                    "weight": weight,
                    "contribution": round(score * weight, 2),
                    "value": factors[factor_name].get("value"),
                })
        
        oracle_score = int(total_score / total_weight) if total_weight > 0 else 50
        
        if oracle_score >= 70:
            signal_type = "strong_buy"
            confidence = "high"
            target_pct = 8 + (oracle_score - 70) * 0.3
        elif oracle_score >= 60:
            signal_type = "buy"
            confidence = "medium"
            target_pct = 5 + (oracle_score - 60) * 0.2
        elif oracle_score <= 30:
            signal_type = "strong_sell"
            confidence = "high"
            target_pct = 8 + (30 - oracle_score) * 0.3
        elif oracle_score <= 40:
            signal_type = "sell"
            confidence = "medium"
            target_pct = 5 + (40 - oracle_score) * 0.2
        else:
            signal_type = "hold"
            confidence = "low"
            target_pct = 3
        
        stop_pct = 3
        
        if signal_type in ["buy", "strong_buy"]:
            target_price = current_price * (1 + target_pct / 100)
            stop_loss = current_price * (1 - stop_pct / 100)
        elif signal_type in ["sell", "strong_sell"]:
            target_price = current_price * (1 - target_pct / 100)
            stop_loss = current_price * (1 + stop_pct / 100)
        else:
            target_price = current_price * 1.03
            stop_loss = current_price * 0.97
        
        risk = abs(current_price - stop_loss)
        reward = abs(target_price - current_price)
        risk_reward = round(reward / risk, 2) if risk > 0 else 1.0
        
        reasoning = self._generate_reasoning(symbol, signal_type, oracle_score, factors)
        
        volatility = factors.get("volatility", {}).get("value", "moderate")
        timeframe = "24h" if volatility in ["very_high", "high"] else "48h"
        expires_hours = 24 if timeframe == "24h" else 48
        
        return {
            "asset_type": "crypto",
            "symbol": symbol,
            "pair": f"{symbol}/USDT",
            "signal_type": signal_type,
            "oracle_score": oracle_score,
            "confidence": confidence,
            "entry_price": round(current_price, 2),
            "target_price": round(target_price, 2),
            "stop_loss": round(stop_loss, 2),
            "target_pct": round(target_pct, 2),
            "stop_pct": round(stop_pct, 2),
            "risk_reward_ratio": risk_reward,
            "factor_breakdown": sorted(factor_breakdown, key=lambda x: x["contribution"], reverse=True),
            "whale_alerts": factors.get("whale_activity", {}).get("signals", []),
            "liquidation_zones": factors.get("liquidation_risk", {}).get("zones", []),
            "funding_rate": factors.get("funding_rate", {}).get("rate_8h", 0),
            "reasoning_summary": reasoning["summary"],
            "reasoning_bullets": reasoning["bullets"],
            "model_version": self.MODEL_VERSION,
            "timeframe": timeframe,
            "expires_at": (datetime.utcnow() + timedelta(hours=expires_hours)).isoformat(),
            "generated_at": datetime.utcnow().isoformat(),
        }
    
    def _generate_reasoning(self, symbol, signal_type, score, factors) -> Dict:
        bullets = []
        
        if score >= 70:
            summary = f"Strong BUY signal for {symbol} (ORACLE Score: {score}/100)"
        elif score >= 60:
            summary = f"BUY signal for {symbol} (ORACLE Score: {score}/100)"
        elif score <= 30:
            summary = f"Strong SELL signal for {symbol} (ORACLE Score: {score}/100)"
        elif score <= 40:
            summary = f"SELL signal for {symbol} (ORACLE Score: {score}/100)"
        else:
            summary = f"HOLD - Neutral outlook for {symbol} (ORACLE Score: {score}/100)"
        
        whale = factors.get("whale_activity", {})
        if whale.get("value") in ["heavy_accumulation", "accumulating"]:
            bullets.append("Whale wallets accumulating - bullish signal")
        elif whale.get("value") in ["heavy_distribution", "distributing"]:
            bullets.append("Whale distribution detected - bearish pressure")
        
        funding = factors.get("funding_rate", {})
        if funding.get("value") == "extreme_short":
            bullets.append("Extreme short positioning - short squeeze potential")
        elif funding.get("value") == "extreme_long":
            bullets.append("Extreme long positioning - long squeeze risk")
        
        flow = factors.get("exchange_flow", {})
        if flow.get("value") == "heavy_outflow":
            bullets.append("Strong exchange outflows - accumulation phase")
        elif flow.get("value") == "heavy_inflow":
            bullets.append("Large exchange inflows - potential selling ahead")
        
        sentiment = factors.get("market_sentiment", {})
        if sentiment.get("value") == "extreme_fear":
            bullets.append("Extreme Fear - contrarian buy opportunity")
        elif sentiment.get("value") == "extreme_greed":
            bullets.append("Extreme Greed - exercise caution")
        
        momentum = factors.get("momentum_24h", {})
        if momentum.get("value") in ["strong_bullish", "bullish"]:
            change = momentum.get("change", 0)
            bullets.append(f"Price up {abs(change):.1f}% in 24h - bullish momentum")
        elif momentum.get("value") in ["strong_bearish", "bearish"]:
            change = momentum.get("change", 0)
            bullets.append(f"Price down {abs(change):.1f}% in 24h - selling pressure")
        
        return {"summary": summary, "bullets": bullets[:6]}
    
    async def get_whale_alerts(self, symbol: str) -> List[Dict]:
        price_data = await coingecko.get_price_data(symbol)
        if not price_data:
            return []
        whale_data = await whale_alert.get_whale_activity(symbol, price_data)
        return whale_data.get("signals", [])
    
    async def get_liquidation_map(self, symbol: str) -> Dict:
        price_data = await coingecko.get_price_data(symbol)
        chart_data = await coingecko.get_market_chart(symbol, days=7)
        if not price_data:
            return {}
        return await liquidation.get_liquidation_data(symbol, price_data, chart_data or {})
    
    async def scan_all_assets(self) -> List[Dict]:
        signals = []
        for symbol in self.SUPPORTED_ASSETS:
            try:
                signal = await self.generate_signal(symbol)
                if signal:
                    signals.append(signal)
            except Exception as e:
                logger.error(f"Error generating signal for {symbol}: {e}")
        signals.sort(key=lambda x: x["oracle_score"], reverse=True)
        return signals


oracle = OracleEngine()
