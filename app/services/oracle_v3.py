"""
ORACLE v3.0 - Institutional-Grade AI Signal Engine
Combines hedge fund quantitative models with on-chain intelligence
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from app.services.data_providers import (
    coingecko, fear_greed, whale_alert, liquidation,
    funding_rate, exchange_flow, open_interest, social_sentiment,
)
from app.services.quant_models import quant_oracle, QuantOracle
from app.core.logging import logger


class OracleEngineV3:
    """
    Enhanced ORACLE with institutional quant models
    
    Model Sources:
    - AQR Capital: Time-Series Momentum (TSMOM)
    - Two Sigma: Statistical Arbitrage, Mean Reversion
    - Renaissance Tech: Multi-factor signal combination
    - Goldman Sachs: Risk metrics (VaR, Sharpe, Sortino)
    - Citadel: Market microstructure, Volume analysis
    """
    
    MODEL_VERSION = "oracle-v3.0.0-institutional"
    
    SUPPORTED_ASSETS = [
        "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", 
        "DOGE", "AVAX", "DOT", "MATIC", "LINK", "UNI",
        "PEPE", "SHIB", "ARB", "OP", "APT", "SUI"
    ]
    
    # Weight allocation across model categories
    MODEL_CATEGORY_WEIGHTS = {
        "quant_models": 0.40,      # Institutional quant models
        "onchain_signals": 0.30,   # Whale, exchange flows, etc.
        "market_sentiment": 0.15,  # Fear & Greed, social
        "technical_factors": 0.15, # Price momentum, volatility
    }
    
    async def analyze_asset(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Full asset analysis with institutional models"""
        symbol = symbol.upper()
        
        if symbol not in self.SUPPORTED_ASSETS:
            logger.warning(f"Unsupported asset: {symbol}")
            return None
        
        logger.info(f"ORACLE v3.0 analyzing {symbol} with institutional models...")
        
        # Fetch market data
        price_data = await coingecko.get_price_data(symbol)
        chart_data = await coingecko.get_market_chart(symbol, days=30)  # Extended for quant models
        
        if not price_data:
            logger.error(f"Failed to fetch price data for {symbol}")
            return None
        
        # Extract price series for quant models
        prices = []
        volumes = []
        if chart_data and "prices" in chart_data:
            prices = [p[1] for p in chart_data["prices"]]
            if "total_volumes" in chart_data:
                volumes = [v[1] for v in chart_data["total_volumes"]]
        
        # Run institutional quant models
        quant_results = {}
        if len(prices) >= 30:
            quant_results = quant_oracle.run_all_models(prices, volumes)
            logger.info(f"Quant models completed for {symbol}: Score {quant_results.get('aggregate', {}).get('quant_score', 'N/A')}")
        
        # Fetch on-chain data
        fng_data = await fear_greed.get_current()
        whale_data = await whale_alert.get_whale_activity(symbol, price_data)
        liq_data = await liquidation.get_liquidation_data(symbol, price_data, chart_data or {})
        funding_data = await funding_rate.get_funding_data(symbol, price_data)
        flow_data = await exchange_flow.get_exchange_flow(symbol, price_data)
        oi_data = await open_interest.get_open_interest(symbol, price_data)
        social_data = await social_sentiment.get_social_sentiment(symbol, price_data)
        
        return {
            "symbol": symbol,
            "price_data": price_data,
            "chart_data": chart_data,
            "quant_results": quant_results,
            "fng_data": fng_data,
            "whale_data": whale_data,
            "liquidation_data": liq_data,
            "funding_data": funding_data,
            "exchange_flow_data": flow_data,
            "open_interest_data": oi_data,
            "social_data": social_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def generate_signal(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Generate comprehensive trading signal"""
        analysis = await self.analyze_asset(symbol)
        
        if not analysis:
            return None
        
        price_data = analysis["price_data"]
        quant_results = analysis.get("quant_results", {})
        current_price = price_data.get("current_price", 0)
        
        if not current_price:
            return None
        
        # Calculate component scores
        scores = self._calculate_component_scores(analysis)
        
        # Calculate weighted ORACLE score
        oracle_score = self._calculate_oracle_score(scores, quant_results)
        
        # Generate signal
        signal_data = self._generate_signal_from_score(
            symbol, oracle_score, current_price, analysis, scores, quant_results
        )
        
        return signal_data
    
    def _calculate_component_scores(self, analysis: Dict) -> Dict:
        """Calculate scores for each component"""
        scores = {}
        
        # On-chain scores
        whale_data = analysis.get("whale_data", {})
        scores["whale_activity"] = whale_data.get("score", 50)
        
        liq_data = analysis.get("liquidation_data", {})
        scores["liquidation_risk"] = 100 - liq_data.get("score", 50)  # Invert (low risk = high score)
        
        funding_data = analysis.get("funding_data", {})
        scores["funding_rate"] = funding_data.get("score", 50)
        
        flow_data = analysis.get("exchange_flow_data", {})
        scores["exchange_flow"] = flow_data.get("score", 50)
        
        oi_data = analysis.get("open_interest_data", {})
        scores["open_interest"] = oi_data.get("score", 50)
        
        # Sentiment scores
        fng_data = analysis.get("fng_data", {})
        fng_value = fng_data.get("value", 50) if fng_data else 50
        # Contrarian: extreme fear = bullish, extreme greed = bearish
        if fng_value < 25:
            scores["market_sentiment"] = 80
        elif fng_value < 40:
            scores["market_sentiment"] = 65
        elif fng_value > 75:
            scores["market_sentiment"] = 25
        elif fng_value > 60:
            scores["market_sentiment"] = 40
        else:
            scores["market_sentiment"] = 50
        
        social_data = analysis.get("social_data", {})
        scores["social_sentiment"] = social_data.get("score", 50)
        
        # Technical scores from price data
        price_data = analysis.get("price_data", {})
        price_change_24h = price_data.get("price_change_24h", 0) or 0
        price_change_7d = price_data.get("price_change_7d", 0) or 0
        
        # Momentum
        if price_change_24h > 5:
            scores["momentum_24h"] = 75
        elif price_change_24h > 2:
            scores["momentum_24h"] = 62
        elif price_change_24h > -2:
            scores["momentum_24h"] = 50
        elif price_change_24h > -5:
            scores["momentum_24h"] = 38
        else:
            scores["momentum_24h"] = 25
        
        # Weekly trend
        if price_change_7d > 10:
            scores["trend_7d"] = 80
        elif price_change_7d > 3:
            scores["trend_7d"] = 65
        elif price_change_7d > -3:
            scores["trend_7d"] = 50
        elif price_change_7d > -10:
            scores["trend_7d"] = 35
        else:
            scores["trend_7d"] = 20
        
        return scores
    
    def _calculate_oracle_score(self, scores: Dict, quant_results: Dict) -> int:
        """Calculate final ORACLE score with institutional model weighting"""
        
        # Get quant aggregate score
        quant_score = 50
        if quant_results and "aggregate" in quant_results:
            quant_score = quant_results["aggregate"].get("quant_score", 50)
        
        # On-chain aggregate
        onchain_scores = [
            scores.get("whale_activity", 50),
            scores.get("liquidation_risk", 50),
            scores.get("funding_rate", 50),
            scores.get("exchange_flow", 50),
            scores.get("open_interest", 50),
        ]
        onchain_score = sum(onchain_scores) / len(onchain_scores)
        
        # Sentiment aggregate
        sentiment_scores = [
            scores.get("market_sentiment", 50),
            scores.get("social_sentiment", 50),
        ]
        sentiment_score = sum(sentiment_scores) / len(sentiment_scores)
        
        # Technical aggregate
        technical_scores = [
            scores.get("momentum_24h", 50),
            scores.get("trend_7d", 50),
        ]
        technical_score = sum(technical_scores) / len(technical_scores)
        
        # Weighted combination
        final_score = (
            quant_score * self.MODEL_CATEGORY_WEIGHTS["quant_models"] +
            onchain_score * self.MODEL_CATEGORY_WEIGHTS["onchain_signals"] +
            sentiment_score * self.MODEL_CATEGORY_WEIGHTS["market_sentiment"] +
            technical_score * self.MODEL_CATEGORY_WEIGHTS["technical_factors"]
        )
        
        return int(max(0, min(100, final_score)))
    
    def _generate_signal_from_score(self, symbol: str, oracle_score: int, 
                                     current_price: float, analysis: Dict,
                                     scores: Dict, quant_results: Dict) -> Dict:
        """Generate complete signal response"""
        
        # Determine signal type
        if oracle_score >= 75:
            signal_type = "strong_buy"
            confidence = "very_high"
            target_pct = 12
        elif oracle_score >= 65:
            signal_type = "buy"
            confidence = "high"
            target_pct = 8
        elif oracle_score >= 55:
            signal_type = "lean_buy"
            confidence = "medium"
            target_pct = 5
        elif oracle_score <= 25:
            signal_type = "strong_sell"
            confidence = "very_high"
            target_pct = 12
        elif oracle_score <= 35:
            signal_type = "sell"
            confidence = "high"
            target_pct = 8
        elif oracle_score <= 45:
            signal_type = "lean_sell"
            confidence = "medium"
            target_pct = 5
        else:
            signal_type = "hold"
            confidence = "low"
            target_pct = 3
        
        # Risk management
        stop_pct = 4  # Tighter stops with institutional models
        
        if signal_type in ["buy", "strong_buy", "lean_buy"]:
            target_price = current_price * (1 + target_pct / 100)
            stop_loss = current_price * (1 - stop_pct / 100)
        elif signal_type in ["sell", "strong_sell", "lean_sell"]:
            target_price = current_price * (1 - target_pct / 100)
            stop_loss = current_price * (1 + stop_pct / 100)
        else:
            target_price = current_price * 1.03
            stop_loss = current_price * 0.97
        
        risk = abs(current_price - stop_loss)
        reward = abs(target_price - current_price)
        risk_reward = round(reward / risk, 2) if risk > 0 else 1.0
        
        # Build reasoning
        reasoning = self._build_reasoning(symbol, signal_type, oracle_score, scores, quant_results)
        
        # Extract key quant insights
        quant_insights = self._extract_quant_insights(quant_results)
        
        # Build response
        price_data = analysis.get("price_data", {})
        
        return {
            "asset_type": "crypto",
            "symbol": symbol,
            "pair": f"{symbol}/USDT",
            "signal_type": signal_type,
            "oracle_score": oracle_score,
            "confidence": confidence,
            "price": round(current_price, 2),
            "price_change_24h": price_data.get("price_change_24h", 0),
            "entry_price": round(current_price, 2),
            "target_price": round(target_price, 2),
            "stop_loss": round(stop_loss, 2),
            "target_pct": round(target_pct, 2),
            "stop_pct": round(stop_pct, 2),
            "risk_reward_ratio": risk_reward,
            "components": {
                "whale_score": scores.get("whale_activity", 50),
                "technical_score": int((scores.get("momentum_24h", 50) + scores.get("trend_7d", 50)) / 2),
                "sentiment_score": scores.get("market_sentiment", 50),
                "liquidation_risk": 100 - scores.get("liquidation_risk", 50),
            },
            "quant_models": {
                "aggregate_score": quant_results.get("aggregate", {}).get("quant_score", 50),
                "signal": quant_results.get("aggregate", {}).get("signal", "HOLD"),
                "models_used": quant_results.get("aggregate", {}).get("models_used", 0),
                "key_insights": quant_insights,
            },
            "detailed_models": {
                "momentum_tsmom": quant_results.get("tsmom", {}),
                "mean_reversion": quant_results.get("bollinger", {}),
                "risk_metrics": {
                    "sharpe": quant_results.get("sharpe", {}),
                    "sortino": quant_results.get("sortino", {}),
                    "var": quant_results.get("var", {}),
                },
                "trend": quant_results.get("dma", {}),
                "volume": quant_results.get("obv", {}),
            },
            "reasoning": reasoning["summary"],
            "reasoning_bullets": reasoning["bullets"],
            "whale_alerts": analysis.get("whale_data", {}).get("signals", []),
            "liquidation_zones": analysis.get("liquidation_data", {}).get("zones", []),
            "funding_rate": analysis.get("funding_data", {}).get("estimated_funding_8h", 0),
            "model_version": self.MODEL_VERSION,
            "institutional_grade": True,
            "generated_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
        }
    
    def _extract_quant_insights(self, quant_results: Dict) -> List[str]:
        """Extract key insights from quant models"""
        insights = []
        
        # TSMOM
        tsmom = quant_results.get("tsmom", {})
        if tsmom.get("confidence") == "high":
            direction = "Bullish" if tsmom.get("signal", 0) > 0 else "Bearish"
            insights.append(f"Strong {direction} momentum signal (TSMOM)")
        
        # Bollinger
        bollinger = quant_results.get("bollinger", {})
        zscore = bollinger.get("zscore", 0)
        if abs(zscore) > 2:
            if zscore < -2:
                insights.append(f"Oversold (Z-Score: {zscore}) - Mean reversion opportunity")
            else:
                insights.append(f"Overbought (Z-Score: {zscore}) - Caution advised")
        
        # Sharpe
        sharpe = quant_results.get("sharpe", {})
        if sharpe.get("quality") == "excellent":
            insights.append(f"Excellent risk-adjusted returns (Sharpe: {sharpe.get('sharpe_ratio', 0)})")
        elif sharpe.get("quality") == "poor":
            insights.append("Poor risk-adjusted returns - Higher risk")
        
        # OBV Divergence
        obv = quant_results.get("obv", {})
        if obv.get("divergence"):
            if "bullish" in obv.get("obv_signal", ""):
                insights.append("Bullish OBV divergence - Smart money accumulating")
            elif "bearish" in obv.get("obv_signal", ""):
                insights.append("Bearish OBV divergence - Smart money distributing")
        
        # DMA Crossover
        dma = quant_results.get("dma", {})
        if dma.get("signal") in ["strong_buy", "strong_sell"]:
            cross = "Golden cross" if dma.get("crossover") == "bullish" else "Death cross"
            insights.append(f"{cross} - {dma.get('signal').replace('_', ' ').title()}")
        
        # VaR
        var_data = quant_results.get("var", {})
        if var_data.get("risk_level") == "high":
            insights.append(f"High volatility risk (VaR 95%: {var_data.get('var_95', 0)}%)")
        
        return insights[:5]  # Top 5 insights
    
    def _build_reasoning(self, symbol: str, signal_type: str, score: int, 
                         scores: Dict, quant_results: Dict) -> Dict:
        """Build comprehensive reasoning"""
        bullets = []
        
        # Quant signal
        quant_signal = quant_results.get("aggregate", {}).get("signal", "HOLD")
        quant_score = quant_results.get("aggregate", {}).get("quant_score", 50)
        bullets.append(f"Institutional quant models: {quant_signal} (Score: {quant_score}/100)")
        
        # Key model signals
        insights = self._extract_quant_insights(quant_results)
        bullets.extend(insights[:3])
        
        # On-chain signals
        whale_score = scores.get("whale_activity", 50)
        if whale_score >= 65:
            bullets.append("Whale accumulation detected - Bullish on-chain signal")
        elif whale_score <= 35:
            bullets.append("Whale distribution detected - Bearish pressure")
        
        # Sentiment
        sentiment = scores.get("market_sentiment", 50)
        if sentiment >= 70:
            bullets.append("Extreme fear in market - Contrarian buy opportunity")
        elif sentiment <= 30:
            bullets.append("Extreme greed - Exercise caution")
        
        # Summary
        if score >= 70:
            summary = f"🟢 STRONG BUY: {symbol} scores {score}/100. Institutional models and on-chain data align bullish."
        elif score >= 55:
            summary = f"🟡 BUY: {symbol} scores {score}/100. Multiple bullish signals detected."
        elif score <= 30:
            summary = f"🔴 STRONG SELL: {symbol} scores {score}/100. Multiple bearish signals."
        elif score <= 45:
            summary = f"🟠 SELL: {symbol} scores {score}/100. Caution advised."
        else:
            summary = f"⚪ HOLD: {symbol} scores {score}/100. Mixed signals - wait for clarity."
        
        return {"summary": summary, "bullets": bullets[:6]}
    
    async def get_supported_assets(self) -> List[str]:
        return self.SUPPORTED_ASSETS


# Singleton
oracle_v3 = OracleEngineV3()
