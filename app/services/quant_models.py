"""
Institutional-Grade Quantitative Models for ORACLE
Based on models used by Renaissance Technologies, Two Sigma, Citadel, and Goldman Sachs
"""
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import math


class MomentumModels:
    """
    Time-Series Momentum (TSMOM) - AQR Capital style
    Cross-Sectional Momentum - Used by most quant funds
    """
    
    @staticmethod
    def tsmom_signal(prices: List[float], lookback: int = 12) -> Dict:
        """
        Time-Series Momentum: If asset outperformed cash over lookback, go long
        Based on Moskowitz, Ooi, Pedersen (2012) - "Time Series Momentum"
        """
        if len(prices) < lookback + 1:
            return {"signal": 0, "score": 50, "confidence": "low"}
        
        # Calculate returns
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        
        # Lookback return
        lookback_return = (prices[-1] - prices[-lookback]) / prices[-lookback]
        
        # Volatility scaling (annualized)
        vol = np.std(returns[-lookback:]) * np.sqrt(365)
        vol = max(vol, 0.01)  # Floor volatility
        
        # Risk-adjusted signal
        signal_strength = lookback_return / vol
        
        # Convert to score (0-100)
        score = 50 + (signal_strength * 25)  # Scale factor
        score = max(0, min(100, score))
        
        return {
            "signal": 1 if lookback_return > 0 else -1,
            "score": round(score),
            "lookback_return": round(lookback_return * 100, 2),
            "volatility": round(vol * 100, 2),
            "signal_strength": round(signal_strength, 3),
            "confidence": "high" if abs(signal_strength) > 1 else "medium" if abs(signal_strength) > 0.5 else "low"
        }
    
    @staticmethod
    def rsi_divergence(prices: List[float], period: int = 14) -> Dict:
        """
        RSI with Divergence Detection
        Professional traders use divergences for reversal signals
        """
        if len(prices) < period + 5:
            return {"rsi": 50, "divergence": None, "score": 50}
        
        # Calculate RSI
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        # Detect divergence (simplified)
        price_trend = prices[-1] - prices[-5]
        rsi_recent = rsi
        
        # Bullish divergence: price making lower lows, RSI making higher lows
        # Bearish divergence: price making higher highs, RSI making lower highs
        divergence = None
        if price_trend < 0 and rsi > 30:
            divergence = "bullish"
        elif price_trend > 0 and rsi < 70:
            divergence = "bearish"
        
        # Score based on oversold/overbought + divergence
        if rsi < 30:
            score = 70 + (30 - rsi)  # Oversold = bullish
        elif rsi > 70:
            score = 30 - (rsi - 70)  # Overbought = bearish
        else:
            score = 50
        
        if divergence == "bullish":
            score += 10
        elif divergence == "bearish":
            score -= 10
        
        return {
            "rsi": round(rsi, 1),
            "divergence": divergence,
            "score": max(0, min(100, round(score))),
            "signal": "oversold" if rsi < 30 else "overbought" if rsi > 70 else "neutral"
        }


class MeanReversionModels:
    """
    Statistical Arbitrage models - Two Sigma / DE Shaw style
    """
    
    @staticmethod
    def bollinger_zscore(prices: List[float], period: int = 20) -> Dict:
        """
        Bollinger Bands with Z-Score
        Mean reversion signal based on standard deviations from mean
        """
        if len(prices) < period:
            return {"zscore": 0, "score": 50, "signal": "neutral"}
        
        recent_prices = prices[-period:]
        mean = sum(recent_prices) / len(recent_prices)
        variance = sum((p - mean) ** 2 for p in recent_prices) / len(recent_prices)
        std = math.sqrt(variance)
        
        if std == 0:
            zscore = 0
        else:
            zscore = (prices[-1] - mean) / std
        
        # Mean reversion: extreme z-scores suggest reversal
        if zscore < -2:
            score = 80  # Very oversold - bullish
            signal = "strong_buy"
        elif zscore < -1:
            score = 65
            signal = "buy"
        elif zscore > 2:
            score = 20  # Very overbought - bearish
            signal = "strong_sell"
        elif zscore > 1:
            score = 35
            signal = "sell"
        else:
            score = 50
            signal = "neutral"
        
        return {
            "zscore": round(zscore, 2),
            "mean": round(mean, 2),
            "std": round(std, 2),
            "upper_band": round(mean + 2 * std, 2),
            "lower_band": round(mean - 2 * std, 2),
            "score": score,
            "signal": signal
        }
    
    @staticmethod
    def ornstein_uhlenbeck(prices: List[float]) -> Dict:
        """
        Ornstein-Uhlenbeck Process - Mean Reversion Speed
        Used by stat arb desks to estimate reversion speed
        """
        if len(prices) < 30:
            return {"half_life": None, "score": 50}
        
        # Estimate mean reversion parameters
        log_prices = [math.log(p) for p in prices if p > 0]
        
        # Simple regression for mean reversion speed
        y = [log_prices[i] - log_prices[i-1] for i in range(1, len(log_prices))]
        x = log_prices[:-1]
        
        n = len(y)
        if n < 10:
            return {"half_life": None, "score": 50}
        
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
        
        if denominator == 0:
            return {"half_life": None, "score": 50}
        
        theta = -numerator / denominator  # Mean reversion speed
        
        if theta <= 0:
            half_life = None
            score = 50
        else:
            half_life = math.log(2) / theta
            # Faster mean reversion = more tradeable
            if half_life < 5:
                score = 70  # Fast reversion
            elif half_life < 15:
                score = 60
            elif half_life < 30:
                score = 50
            else:
                score = 40  # Slow reversion
        
        return {
            "half_life": round(half_life, 1) if half_life else None,
            "mean_reversion_speed": round(theta, 4) if theta > 0 else 0,
            "score": score,
            "tradeable": half_life is not None and half_life < 30
        }


class RiskModels:
    """
    Risk management models - Goldman Sachs / JPMorgan style
    """
    
    @staticmethod
    def value_at_risk(prices: List[float], confidence: float = 0.95) -> Dict:
        """
        Historical VaR - Standard risk metric
        """
        if len(prices) < 30:
            return {"var_95": None, "score": 50}
        
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        
        # Historical VaR
        sorted_returns = sorted(returns)
        var_index = int((1 - confidence) * len(sorted_returns))
        var = abs(sorted_returns[var_index])
        
        # Expected Shortfall (CVaR)
        cvar = abs(sum(sorted_returns[:var_index+1]) / (var_index + 1)) if var_index > 0 else var
        
        # Score: lower risk = higher score for long positions
        if var < 0.03:
            score = 70  # Low risk
        elif var < 0.05:
            score = 60
        elif var < 0.08:
            score = 50
        elif var < 0.12:
            score = 40
        else:
            score = 30  # High risk
        
        return {
            "var_95": round(var * 100, 2),  # As percentage
            "cvar_95": round(cvar * 100, 2),
            "max_drawdown": round(min(returns) * 100, 2),
            "score": score,
            "risk_level": "low" if var < 0.03 else "medium" if var < 0.08 else "high"
        }
    
    @staticmethod
    def sharpe_ratio(prices: List[float], risk_free_rate: float = 0.05) -> Dict:
        """
        Sharpe Ratio - Risk-adjusted returns
        """
        if len(prices) < 30:
            return {"sharpe": None, "score": 50}
        
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        
        mean_return = sum(returns) / len(returns)
        std_return = np.std(returns)
        
        # Annualize
        annual_return = mean_return * 365
        annual_vol = std_return * np.sqrt(365)
        
        if annual_vol == 0:
            sharpe = 0
        else:
            sharpe = (annual_return - risk_free_rate) / annual_vol
        
        # Score based on Sharpe
        if sharpe > 2:
            score = 85  # Excellent
        elif sharpe > 1:
            score = 70
        elif sharpe > 0.5:
            score = 60
        elif sharpe > 0:
            score = 50
        else:
            score = 35  # Negative Sharpe
        
        return {
            "sharpe_ratio": round(sharpe, 2),
            "annual_return": round(annual_return * 100, 2),
            "annual_volatility": round(annual_vol * 100, 2),
            "score": score,
            "quality": "excellent" if sharpe > 2 else "good" if sharpe > 1 else "average" if sharpe > 0 else "poor"
        }
    
    @staticmethod
    def sortino_ratio(prices: List[float], risk_free_rate: float = 0.05) -> Dict:
        """
        Sortino Ratio - Downside risk adjusted returns
        Better than Sharpe for asymmetric returns (crypto)
        """
        if len(prices) < 30:
            return {"sortino": None, "score": 50}
        
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        
        mean_return = sum(returns) / len(returns)
        
        # Downside deviation (only negative returns)
        negative_returns = [r for r in returns if r < 0]
        if not negative_returns:
            downside_dev = 0.001
        else:
            downside_dev = np.std(negative_returns) * np.sqrt(365)
        
        annual_return = mean_return * 365
        
        if downside_dev == 0:
            sortino = 0
        else:
            sortino = (annual_return - risk_free_rate) / downside_dev
        
        if sortino > 3:
            score = 85
        elif sortino > 2:
            score = 75
        elif sortino > 1:
            score = 60
        elif sortino > 0:
            score = 50
        else:
            score = 35
        
        return {
            "sortino_ratio": round(sortino, 2),
            "downside_deviation": round(downside_dev * 100, 2),
            "score": score
        }


class TrendModels:
    """
    Trend Following Models - CTA / Managed Futures style
    """
    
    @staticmethod
    def dual_moving_average(prices: List[float], fast: int = 10, slow: int = 30) -> Dict:
        """
        Dual Moving Average Crossover
        Classic trend following signal
        """
        if len(prices) < slow:
            return {"signal": "neutral", "score": 50}
        
        fast_ma = sum(prices[-fast:]) / fast
        slow_ma = sum(prices[-slow:]) / slow
        
        current_price = prices[-1]
        
        # Signal
        if fast_ma > slow_ma and current_price > fast_ma:
            signal = "strong_buy"
            score = 75
        elif fast_ma > slow_ma:
            signal = "buy"
            score = 65
        elif fast_ma < slow_ma and current_price < fast_ma:
            signal = "strong_sell"
            score = 25
        elif fast_ma < slow_ma:
            signal = "sell"
            score = 35
        else:
            signal = "neutral"
            score = 50
        
        # Trend strength
        trend_strength = abs(fast_ma - slow_ma) / slow_ma * 100
        
        return {
            "fast_ma": round(fast_ma, 2),
            "slow_ma": round(slow_ma, 2),
            "signal": signal,
            "score": score,
            "trend_strength": round(trend_strength, 2),
            "crossover": "bullish" if fast_ma > slow_ma else "bearish"
        }
    
    @staticmethod
    def adx_trend_strength(prices: List[float], highs: List[float], lows: List[float], period: int = 14) -> Dict:
        """
        Average Directional Index - Trend Strength
        Used by CTAs to measure trend quality
        """
        if len(prices) < period + 1:
            return {"adx": None, "score": 50}
        
        # Simplified ADX calculation
        tr_list = []
        plus_dm_list = []
        minus_dm_list = []
        
        for i in range(1, len(prices)):
            high_diff = highs[i] - highs[i-1] if i < len(highs) else 0
            low_diff = lows[i-1] - lows[i] if i < len(lows) else 0
            
            plus_dm = high_diff if high_diff > low_diff and high_diff > 0 else 0
            minus_dm = low_diff if low_diff > high_diff and low_diff > 0 else 0
            
            tr = max(
                highs[i] - lows[i] if i < len(highs) and i < len(lows) else abs(prices[i] - prices[i-1]),
                abs(highs[i] - prices[i-1]) if i < len(highs) else 0,
                abs(lows[i] - prices[i-1]) if i < len(lows) else 0
            )
            
            tr_list.append(tr)
            plus_dm_list.append(plus_dm)
            minus_dm_list.append(minus_dm)
        
        if len(tr_list) < period:
            return {"adx": None, "score": 50}
        
        # Smoothed averages
        atr = sum(tr_list[-period:]) / period
        plus_di = (sum(plus_dm_list[-period:]) / period) / atr * 100 if atr > 0 else 0
        minus_di = (sum(minus_dm_list[-period:]) / period) / atr * 100 if atr > 0 else 0
        
        # DX and ADX
        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100 if (plus_di + minus_di) > 0 else 0
        adx = dx  # Simplified
        
        # Score based on trend strength and direction
        if adx > 40:
            trend_quality = "strong"
            base_score = 70 if plus_di > minus_di else 30
        elif adx > 25:
            trend_quality = "moderate"
            base_score = 60 if plus_di > minus_di else 40
        else:
            trend_quality = "weak"
            base_score = 50
        
        return {
            "adx": round(adx, 1),
            "plus_di": round(plus_di, 1),
            "minus_di": round(minus_di, 1),
            "trend_quality": trend_quality,
            "trend_direction": "bullish" if plus_di > minus_di else "bearish",
            "score": base_score
        }


class VolumeModels:
    """
    Volume Analysis - Market Microstructure
    """
    
    @staticmethod
    def volume_profile(prices: List[float], volumes: List[float]) -> Dict:
        """
        Volume-Weighted Analysis
        Identifies key price levels with high volume
        """
        if len(prices) < 10 or len(volumes) < 10:
            return {"vwap": None, "score": 50}
        
        # VWAP
        total_volume = sum(volumes)
        if total_volume == 0:
            return {"vwap": None, "score": 50}
        
        vwap = sum(p * v for p, v in zip(prices, volumes)) / total_volume
        
        current_price = prices[-1]
        deviation = (current_price - vwap) / vwap * 100
        
        # Score: price below VWAP = potential buy, above = potential sell
        if deviation < -3:
            score = 70  # Good buy zone
            signal = "below_vwap"
        elif deviation < 0:
            score = 60
            signal = "slightly_below_vwap"
        elif deviation > 3:
            score = 30  # Extended
            signal = "above_vwap"
        elif deviation > 0:
            score = 40
            signal = "slightly_above_vwap"
        else:
            score = 50
            signal = "at_vwap"
        
        # Volume trend
        recent_vol = sum(volumes[-5:]) / 5
        older_vol = sum(volumes[-20:-5]) / 15 if len(volumes) >= 20 else recent_vol
        vol_change = (recent_vol - older_vol) / older_vol * 100 if older_vol > 0 else 0
        
        return {
            "vwap": round(vwap, 2),
            "current_price": round(current_price, 2),
            "deviation_pct": round(deviation, 2),
            "signal": signal,
            "volume_trend": "increasing" if vol_change > 20 else "decreasing" if vol_change < -20 else "stable",
            "score": score
        }
    
    @staticmethod
    def on_balance_volume(prices: List[float], volumes: List[float]) -> Dict:
        """
        On-Balance Volume (OBV)
        Volume precedes price - smart money indicator
        """
        if len(prices) < 20 or len(volumes) < 20:
            return {"obv_signal": "neutral", "score": 50}
        
        obv = 0
        obv_list = []
        
        for i in range(1, len(prices)):
            if prices[i] > prices[i-1]:
                obv += volumes[i]
            elif prices[i] < prices[i-1]:
                obv -= volumes[i]
            obv_list.append(obv)
        
        # OBV trend vs price trend
        obv_change = obv_list[-1] - obv_list[-10] if len(obv_list) >= 10 else 0
        price_change = prices[-1] - prices[-10] if len(prices) >= 10 else 0
        
        # Divergence detection
        if price_change < 0 and obv_change > 0:
            signal = "bullish_divergence"  # Smart money accumulating
            score = 75
        elif price_change > 0 and obv_change < 0:
            signal = "bearish_divergence"  # Smart money distributing
            score = 25
        elif price_change > 0 and obv_change > 0:
            signal = "confirmed_uptrend"
            score = 65
        elif price_change < 0 and obv_change < 0:
            signal = "confirmed_downtrend"
            score = 35
        else:
            signal = "neutral"
            score = 50
        
        return {
            "obv_signal": signal,
            "obv_trend": "up" if obv_change > 0 else "down",
            "price_trend": "up" if price_change > 0 else "down",
            "divergence": signal.endswith("divergence"),
            "score": score
        }


class QuantOracle:
    """
    Master class combining all institutional models
    """
    
    def __init__(self):
        self.momentum = MomentumModels()
        self.mean_reversion = MeanReversionModels()
        self.risk = RiskModels()
        self.trend = TrendModels()
        self.volume = VolumeModels()
    
    def run_all_models(self, prices: List[float], volumes: List[float] = None, 
                       highs: List[float] = None, lows: List[float] = None) -> Dict:
        """
        Run all institutional models and aggregate signals
        """
        if volumes is None:
            volumes = [1000000] * len(prices)  # Default volume
        if highs is None:
            highs = prices
        if lows is None:
            lows = prices
        
        results = {}
        
        # Momentum Models
        results["tsmom"] = self.momentum.tsmom_signal(prices)
        results["rsi"] = self.momentum.rsi_divergence(prices)
        
        # Mean Reversion Models
        results["bollinger"] = self.mean_reversion.bollinger_zscore(prices)
        results["ou_process"] = self.mean_reversion.ornstein_uhlenbeck(prices)
        
        # Risk Models
        results["var"] = self.risk.value_at_risk(prices)
        results["sharpe"] = self.risk.sharpe_ratio(prices)
        results["sortino"] = self.risk.sortino_ratio(prices)
        
        # Trend Models
        results["dma"] = self.trend.dual_moving_average(prices)
        results["adx"] = self.trend.adx_trend_strength(prices, highs, lows)
        
        # Volume Models
        results["vwap"] = self.volume.volume_profile(prices, volumes)
        results["obv"] = self.volume.on_balance_volume(prices, volumes)
        
        # Aggregate Score
        model_weights = {
            "tsmom": 0.15,
            "rsi": 0.08,
            "bollinger": 0.10,
            "ou_process": 0.05,
            "var": 0.08,
            "sharpe": 0.10,
            "sortino": 0.08,
            "dma": 0.12,
            "adx": 0.08,
            "vwap": 0.08,
            "obv": 0.08,
        }
        
        total_score = 0
        total_weight = 0
        
        for model, weight in model_weights.items():
            if model in results and "score" in results[model]:
                total_score += results[model]["score"] * weight
                total_weight += weight
        
        aggregate_score = int(total_score / total_weight) if total_weight > 0 else 50
        
        # Signal classification
        if aggregate_score >= 70:
            signal = "STRONG BUY"
            confidence = "HIGH"
        elif aggregate_score >= 60:
            signal = "BUY"
            confidence = "MEDIUM"
        elif aggregate_score <= 30:
            signal = "STRONG SELL"
            confidence = "HIGH"
        elif aggregate_score <= 40:
            signal = "SELL"
            confidence = "MEDIUM"
        else:
            signal = "HOLD"
            confidence = "LOW"
        
        results["aggregate"] = {
            "quant_score": aggregate_score,
            "signal": signal,
            "confidence": confidence,
            "models_used": len([r for r in results.values() if isinstance(r, dict) and "score" in r])
        }
        
        return results


# Singleton instance
quant_oracle = QuantOracle()
