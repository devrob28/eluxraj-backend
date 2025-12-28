"""
Trade Intelligence Service V2
Institutional-grade AI-powered trade playbooks and chart analysis
"""
import httpx
import json
import base64
from typing import Dict, Optional, List
from datetime import datetime, timezone, timedelta
from app.core.config import settings
from app.core.logging import logger


class TradeIntelligenceService:
    """AI-powered trade analysis and playbook generation"""
    
    ANTHROPIC_API = "https://api.anthropic.com/v1/messages"
    
    def __init__(self):
        self.api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
    
    async def generate_playbook(
        self,
        asset: str,
        asset_type: str,
        timeframe: str,
        current_price: float,
        market_data: Dict = None
    ) -> Dict:
        """Generate a complete trade playbook for an asset"""
        
        # Timeframe context
        tf_context = {
            "15m": "scalping/intraday - focus on immediate momentum, tight stops, quick targets",
            "1h": "intraday swing - balance momentum with structure, 4-8 hour hold times",
            "4h": "swing trading - focus on trend structure, 1-5 day hold times typical",
            "1d": "position trading - focus on major levels, weekly trends, 1-4 week holds",
            "1w": "macro positioning - focus on monthly/quarterly trends, multi-week to month holds"
        }.get(timeframe, "swing trading perspective")
        
        prompt = f"""You are a senior quantitative analyst at a top-tier hedge fund with 15+ years experience trading {asset_type} markets. You combine technical analysis, market structure analysis, order flow concepts, and risk management into actionable trade intelligence.

═══════════════════════════════════════════════════════════════
ANALYSIS REQUEST
═══════════════════════════════════════════════════════════════
ASSET: {asset}
ASSET TYPE: {asset_type}
TIMEFRAME: {timeframe} ({tf_context})
CURRENT PRICE: ${current_price:,.2f}
ANALYSIS TIME: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
{f"SUPPLEMENTAL DATA: {json.dumps(market_data)}" if market_data else ""}

═══════════════════════════════════════════════════════════════
YOUR ANALYSIS FRAMEWORK
═══════════════════════════════════════════════════════════════

1. MARKET STRUCTURE ANALYSIS
   - Identify current trend (HH/HL for uptrend, LH/LL for downtrend)
   - Locate key swing points and structure breaks
   - Determine if price is in markup, markdown, accumulation, or distribution

2. KEY LEVEL IDENTIFICATION  
   - Major support/resistance from recent price action
   - Round psychological numbers
   - Previous day/week/month highs and lows
   - Areas of high volume/liquidity

3. PATTERN RECOGNITION
   - Classic patterns: triangles, wedges, channels, head & shoulders
   - Candlestick patterns: engulfing, doji, hammers at key levels
   - Momentum divergences if applicable

4. TRADE SETUP CONSTRUCTION
   - Entry zone: Where institutional buyers/sellers likely step in
   - Stop loss: Beyond structure that invalidates the thesis
   - Targets: Scaled exits at logical resistance/support levels
   - Risk/Reward: Minimum 2:1 for valid setups

5. SCENARIO PLANNING
   - Map out 3 bullish and 3 bearish scenarios with specific triggers
   - Assign realistic probabilities that reflect uncertainty
   - Include invalidation conditions for each scenario

═══════════════════════════════════════════════════════════════
CRITICAL RULES
═══════════════════════════════════════════════════════════════
- PRICES MUST BE REALISTIC relative to current price ${current_price:,.2f}
- Entry zones should be within 5% of current price for {timeframe} timeframe
- Stop losses should be 2-8% from entry depending on timeframe
- Take profits should be at logical levels (prior highs/lows, fib extensions, round numbers)
- Risk/Reward must be calculated as: (TP1 - Entry) / (Entry - StopLoss)
- Probabilities should reflect genuine uncertainty - avoid 90%+ confidence
- This is DECISION INTELLIGENCE, not financial advice

═══════════════════════════════════════════════════════════════
RESPOND WITH VALID JSON ONLY (no markdown, no explanation outside JSON):
═══════════════════════════════════════════════════════════════

{{
    "market_bias": "bullish|bearish|neutral",
    "bias_strength": <50-85 realistic range>,
    "market_structure": "trending_up|trending_down|ranging|breakout|breakdown|accumulation|distribution",
    "trend_analysis": "<2-3 sentence description of current trend and key levels>",
    "entry_zone": {{
        "low": <price within 3% below current>,
        "high": <price within 2% above current>,
        "rationale": "<specific technical reason for this zone>"
    }},
    "stop_loss": {{
        "price": <price below entry zone>,
        "percentage": <2-8% from mid entry>,
        "rationale": "<what structure this is below/above>"
    }},
    "take_profits": [
        {{"level": "TP1", "price": <conservative target>, "probability": <50-70>, "rationale": "<nearest resistance/support>"}},
        {{"level": "TP2", "price": <moderate target>, "probability": <30-50>, "rationale": "<next major level>"}},
        {{"level": "TP3", "price": <aggressive target>, "probability": <15-35>, "rationale": "<extended target>"}}
    ],
    "position_sizing": {{
        "suggested_risk": "1-2% of portfolio",
        "scaling_strategy": "Enter 50% at zone low, 50% at zone high OR scale in on confirmation"
    }},
    "risk_reward_ratio": <calculated RR to TP1, minimum 2.0>,
    "probability_score": <40-75 realistic range>,
    "confidence_score": <50-80 realistic range>,
    "pattern_detected": "<specific pattern or 'No clear pattern - structure-based setup'>",
    "key_levels": {{
        "major_resistance": [<price1>, <price2>],
        "major_support": [<price1>, <price2>],
        "pivot_point": <key decision level>
    }},
    "bullish_scenarios": [
        {{
            "name": "<specific scenario name>",
            "probability": <20-50>,
            "trigger": "<exact price action or event that triggers this>",
            "target": <price target>,
            "explanation": "<detailed 2-3 sentence reasoning with specific levels>"
        }},
        {{
            "name": "<scenario 2>",
            "probability": <15-40>,
            "trigger": "<trigger>",
            "target": <target>,
            "explanation": "<reasoning>"
        }},
        {{
            "name": "<scenario 3>",
            "probability": <10-30>,
            "trigger": "<trigger>",
            "target": <target>,
            "explanation": "<reasoning>"
        }}
    ],
    "bearish_scenarios": [
        {{
            "name": "<specific scenario name>",
            "probability": <20-50>,
            "trigger": "<exact price action or event>",
            "target": <downside target>,
            "explanation": "<detailed reasoning>"
        }},
        {{
            "name": "<scenario 2>",
            "probability": <15-40>,
            "trigger": "<trigger>",
            "target": <target>,
            "explanation": "<reasoning>"
        }},
        {{
            "name": "<scenario 3>",
            "probability": <10-30>,
            "trigger": "<trigger>",
            "target": <target>,
            "explanation": "<reasoning>"
        }}
    ],
    "invalidation_conditions": [
        "<specific price level or condition that invalidates bullish thesis>",
        "<secondary invalidation>",
        "<time-based invalidation if applicable>"
    ],
    "invalidation_price": <price where entire thesis fails>,
    "trade_management": {{
        "entry_confirmation": "<what to look for before entering>",
        "move_stop_to_breakeven": "<condition to move stop>",
        "partial_profit_taking": "Take 33% at TP1, 33% at TP2, let 34% run to TP3"
    }},
    "reasoning": "<comprehensive 4-6 sentence analysis explaining the setup, why levels matter, what you're watching for, and key risks. Be specific about price levels and market structure.>"
}}"""

        return await self._call_ai(prompt)
    
    async def analyze_chart_image(
        self,
        image_path: str,
        asset: str,
        timeframe: str
    ) -> Dict:
        """Analyze a chart image and return trade intelligence"""
        
        # Read and encode image
        try:
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            # Detect media type
            if image_path.lower().endswith(".png"):
                media_type = "image/png"
            else:
                media_type = "image/jpeg"
        except Exception as e:
            logger.error(f"Failed to read image: {e}")
            return self._fallback_analysis(asset, timeframe)
        
        prompt = f"""You are an elite technical analyst and Fibonacci specialist with 20+ years of institutional trading experience. You combine classical chart analysis with advanced Fibonacci techniques used by professional traders.

═══════════════════════════════════════════════════════════════
CHART ANALYSIS REQUEST
═══════════════════════════════════════════════════════════════
ASSET: {asset}
TIMEFRAME: {timeframe}

Analyze this chart with institutional-grade precision. Apply both classical technical analysis AND Fibonacci analysis.

═══════════════════════════════════════════════════════════════
YOUR ANALYSIS FRAMEWORK
═══════════════════════════════════════════════════════════════

1. TREND IDENTIFICATION
   - Determine primary trend direction (HH/HL = uptrend, LH/LL = downtrend)
   - Identify the most recent significant swing high and swing low
   - Note any trend line breaks or structure shifts

2. FIBONACCI RETRACEMENT ANALYSIS
   - Identify the most recent impulse move (swing low to swing high OR swing high to swing low)
   - Calculate key Fibonacci retracement levels:
     * 0.236 (23.6%) - Shallow retracement, strong trend
     * 0.382 (38.2%) - Common retracement in strong trends
     * 0.500 (50.0%) - Psychological midpoint
     * 0.618 (61.8%) - Golden ratio, most important level
     * 0.786 (78.6%) - Deep retracement, last defense
   - Note which Fib level price is currently at or approaching
   - Identify confluence zones where Fib levels align with S/R

3. FIBONACCI EXTENSION TARGETS
   - For profit targets, calculate extensions from the retracement:
     * 1.272 extension - Conservative target
     * 1.618 extension - Golden ratio target (most common)
     * 2.000 extension - Measured move target
     * 2.618 extension - Extended target

4. PATTERN RECOGNITION
   - Classical: triangles, wedges, channels, double tops/bottoms, H&S
   - Harmonic patterns: Gartley, Bat, Butterfly, Crab (if visible)
   - Note pattern completion percentage

5. KEY LEVEL CONFLUENCE
   - Where do Fibonacci levels align with horizontal S/R?
   - Where do Fibonacci levels align with trend lines?
   - These confluence zones are highest probability areas

6. ENTRY OPTIMIZATION
   - Best entries occur at Fib levels with confluence
   - 0.618 retracement + horizontal support = high probability long
   - 0.618 retracement + horizontal resistance = high probability short

═══════════════════════════════════════════════════════════════
FIBONACCI TRADING RULES
═══════════════════════════════════════════════════════════════
- In UPTREND: Look for longs at 0.382, 0.500, or 0.618 retracements
- In DOWNTREND: Look for shorts at 0.382, 0.500, or 0.618 retracements  
- Stop loss goes beyond the 0.786 or recent swing point
- First target: 0.000 (return to swing high/low)
- Second target: -0.272 or 1.272 extension
- Third target: -0.618 or 1.618 extension
- Risk/Reward should be minimum 2:1

═══════════════════════════════════════════════════════════════
CRITICAL RULES
═══════════════════════════════════════════════════════════════
- Read ACTUAL prices from the chart Y-axis
- Calculate Fibonacci levels based on visible swing points
- Only recommend trades at Fibonacci levels with confluence
- If no clear Fib setup exists, recommend "wait"
- This is decision intelligence, NOT financial advice

═══════════════════════════════════════════════════════════════
RESPOND WITH VALID JSON ONLY:
═══════════════════════════════════════════════════════════════

{{
    "chart_quality": "clear|moderate|poor",
    "trend_direction": "uptrend|downtrend|sideways",
    "trend_strength": "strong|moderate|weak",
    "pattern_detected": "<specific pattern name or 'No clear pattern'>",
    "pattern_completion": "forming|near_completion|completed|failed",
    "market_structure": "trending_up|trending_down|ranging|breakout|breakdown|unclear",
    "trend_description": "<2-3 sentence description of trend and structure>",
    "swing_points": {{
        "recent_swing_high": "<price from chart>",
        "recent_swing_low": "<price from chart>",
        "current_price": "<approximate current price>"
    }},
    "fibonacci_analysis": {{
        "impulse_direction": "up|down",
        "impulse_start": "<swing low/high price>",
        "impulse_end": "<swing high/low price>",
        "fib_236": "<calculated 23.6% level>",
        "fib_382": "<calculated 38.2% level>",
        "fib_500": "<calculated 50% level>",
        "fib_618": "<calculated 61.8% level - GOLDEN RATIO>",
        "fib_786": "<calculated 78.6% level>",
        "current_fib_zone": "<which fib level is price at or near>",
        "fib_confluence": "<describe any confluence with S/R levels>"
    }},
    "fibonacci_extensions": {{
        "ext_1272": "<1.272 extension price>",
        "ext_1618": "<1.618 extension price - GOLDEN TARGET>",
        "ext_2000": "<2.0 extension price>"
    }},
    "key_levels": {{
        "support": ["<price1>", "<price2>"],
        "resistance": ["<price1>", "<price2>"],
        "fib_support_confluence": "<fib level that aligns with support>",
        "fib_resistance_confluence": "<fib level that aligns with resistance>"
    }},
    "candlestick_notes": "<significant candle patterns at key levels/fib zones>",
    "volume_analysis": "<volume behavior if visible>",
    "bullish_scenarios": [
        {{
            "name": "<scenario name>",
            "probability": <20-60>,
            "trigger": "<specific price action at fib level>",
            "target": "<fib extension or key level>",
            "explanation": "<reasoning with fib levels>"
        }},
        {{
            "name": "<scenario 2>",
            "probability": <15-45>,
            "trigger": "<trigger>",
            "target": "<target>",
            "explanation": "<reasoning>"
        }},
        {{
            "name": "<scenario 3>",
            "probability": <10-35>,
            "trigger": "<trigger>",
            "target": "<target>",
            "explanation": "<reasoning>"
        }}
    ],
    "bearish_scenarios": [
        {{
            "name": "<scenario name>",
            "probability": <20-60>,
            "trigger": "<specific price action>",
            "target": "<fib extension or key level>",
            "explanation": "<reasoning with fib levels>"
        }},
        {{
            "name": "<scenario 2>",
            "probability": <15-45>,
            "trigger": "<trigger>",
            "target": "<target>",
            "explanation": "<reasoning>"
        }},
        {{
            "name": "<scenario 3>",
            "probability": <10-35>,
            "trigger": "<trigger>",
            "target": "<target>",
            "explanation": "<reasoning>"
        }}
    ],
    "trade_recommendation": "long|short|wait|no_trade",
    "trade_setup": {{
        "bias": "bullish|bearish|neutral",
        "entry_zone": "<fib level or price zone>",
        "entry_trigger": "<what confirms entry>",
        "stop_loss": "<beyond fib 0.786 or structure>",
        "take_profit_1": "<fib extension 1.272 or key level>",
        "take_profit_2": "<fib extension 1.618 or key level>",
        "take_profit_3": "<fib extension 2.0 or extended target>",
        "risk_reward": "<calculated RR ratio>"
    }},
    "entry_confirmation": "<what to wait for: candle close, volume, etc>",
    "confidence_score": <40-85>,
    "fib_quality": "<how clean are the fib levels: excellent|good|moderate|poor>",
    "invalidation_conditions": [
        "<price level that invalidates the setup>",
        "<secondary invalidation>"
    ],
    "reasoning": "<5-7 sentence comprehensive analysis incorporating Fibonacci levels, confluence zones, pattern recognition, and risk assessment. Be specific about which fib levels matter most and why.>"
}}"""

        return await self._call_ai_with_image(prompt, image_data, media_type)
    
    async def _call_ai(self, prompt: str) -> Dict:
        """Call Anthropic API for text analysis"""
        if not self.api_key:
            logger.warning("Anthropic API key not configured")
            return self._fallback_playbook()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.ANTHROPIC_API,
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 4096,
                        "messages": [{"role": "user", "content": prompt}]
                    },
                    timeout=90.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["content"][0]["text"]
                    return self._parse_json_response(content)
                else:
                    logger.error(f"Anthropic API error: {response.status_code} - {response.text}")
                    return self._fallback_playbook()
        except Exception as e:
            logger.error(f"AI call failed: {e}")
            return self._fallback_playbook()
    
    async def _call_ai_with_image(self, prompt: str, image_data: str, media_type: str) -> Dict:
        """Call Anthropic API with image"""
        if not self.api_key:
            logger.warning("Anthropic API key not configured")
            return self._fallback_analysis("", "")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.ANTHROPIC_API,
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 4096,
                        "messages": [{
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": media_type,
                                        "data": image_data
                                    }
                                },
                                {"type": "text", "text": prompt}
                            ]
                        }]
                    },
                    timeout=120.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["content"][0]["text"]
                    return self._parse_json_response(content)
                else:
                    logger.error(f"Anthropic API error: {response.status_code} - {response.text}")
                    return self._fallback_analysis("", "")
        except Exception as e:
            logger.error(f"AI image call failed: {e}")
            return self._fallback_analysis("", "")
    
    def _parse_json_response(self, content: str) -> Dict:
        """Parse JSON from AI response"""
        try:
            # Try direct parse
            return json.loads(content)
        except:
            # Try to extract JSON from markdown code block
            import re
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    pass
            # Try to find JSON object
            match = re.search(r'\{[\s\S]*\}', content)
            if match:
                try:
                    return json.loads(match.group(0))
                except:
                    pass
        logger.error(f"Failed to parse AI response: {content[:500]}")
        return self._fallback_playbook()
    
    def _fallback_playbook(self) -> Dict:
        """Return fallback when AI unavailable"""
        return {
            "market_bias": "neutral",
            "bias_strength": 50,
            "entry_zone": {"low": 0, "high": 0, "rationale": "AI analysis temporarily unavailable - please try again"},
            "stop_loss": {"price": 0, "percentage": 5, "rationale": "Default 5%"},
            "take_profits": [
                {"level": "TP1", "price": 0, "probability": 33, "rationale": "Pending"},
                {"level": "TP2", "price": 0, "probability": 33, "rationale": "Pending"},
                {"level": "TP3", "price": 0, "probability": 33, "rationale": "Pending"}
            ],
            "risk_reward_ratio": 0,
            "probability_score": 50,
            "confidence_score": 0,
            "bullish_scenarios": [{"name": "Analysis Pending", "probability": 33, "trigger": "N/A", "target": 0, "explanation": "AI analysis temporarily unavailable. Please try again in a moment."}],
            "bearish_scenarios": [{"name": "Analysis Pending", "probability": 33, "trigger": "N/A", "target": 0, "explanation": "AI analysis temporarily unavailable. Please try again in a moment."}],
            "invalidation_conditions": ["Analysis unavailable - please retry"],
            "invalidation_price": 0,
            "pattern_detected": "Pending",
            "market_structure": "unclear",
            "reasoning": "AI analysis temporarily unavailable. This could be due to high demand or a temporary service issue. Please try again in a few moments.",
            "error": True
        }
    
    def _fallback_analysis(self, asset: str, timeframe: str) -> Dict:
        """Return fallback for chart analysis"""
        return {
            "chart_quality": "unknown",
            "pattern_detected": "Analysis pending",
            "market_structure": "unclear",
            "key_levels": {"support": [], "resistance": []},
            "bullish_scenarios": [{"name": "Analysis Pending", "probability": 33, "trigger": "N/A", "target": "N/A", "explanation": "AI analysis temporarily unavailable"}],
            "bearish_scenarios": [{"name": "Analysis Pending", "probability": 33, "trigger": "N/A", "target": "N/A", "explanation": "AI analysis temporarily unavailable"}],
            "trade_recommendation": "wait",
            "trade_setup": {
                "entry": "N/A",
                "stop_loss": "N/A",
                "take_profit_1": "N/A",
                "take_profit_2": "N/A",
                "take_profit_3": "N/A",
                "risk_reward": 0
            },
            "confidence_score": 0,
            "invalidation_conditions": ["Analysis unavailable"],
            "reasoning": "AI analysis temporarily unavailable. Please try again.",
            "error": True
        }


# Singleton instance
trade_intelligence = TradeIntelligenceService()
