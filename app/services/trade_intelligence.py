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
        
        prompt = f"""You are a senior technical analyst with 20+ years of chart reading experience. You've analyzed thousands of charts across crypto, stocks, and forex markets.

═══════════════════════════════════════════════════════════════
CHART ANALYSIS REQUEST
═══════════════════════════════════════════════════════════════
ASSET: {asset}
TIMEFRAME: {timeframe}

Analyze this chart image with extreme precision. Study every candle, every level, every pattern.

═══════════════════════════════════════════════════════════════
YOUR ANALYSIS PROCESS
═══════════════════════════════════════════════════════════════

1. FIRST LOOK - What's the dominant trend visible in the chart?
2. STRUCTURE - Identify swing highs and lows. Is it making HH/HL or LH/LL?
3. KEY LEVELS - Find the most obvious support and resistance from the chart
4. PATTERNS - Look for: triangles, wedges, channels, double tops/bottoms, H&S
5. CANDLESTICKS - Note any significant candle patterns at key levels
6. CURRENT POSITION - Where is price relative to key levels right now?
7. TRADE SETUP - Based on all above, is there a valid setup?

═══════════════════════════════════════════════════════════════
CRITICAL RULES
═══════════════════════════════════════════════════════════════
- Read the ACTUAL prices from the chart Y-axis
- If you cannot clearly see prices, estimate based on visible numbers
- Only suggest a trade if there's a clear setup with defined risk
- If the chart is unclear or no setup exists, recommend "wait"
- Be specific about levels you can see in the chart
- This is decision intelligence, NOT financial advice

═══════════════════════════════════════════════════════════════
RESPOND WITH VALID JSON ONLY:
═══════════════════════════════════════════════════════════════

{{
    "chart_quality": "clear|moderate|poor",
    "pattern_detected": "<specific pattern name or 'No clear pattern'>",
    "pattern_completion": "<how complete is the pattern: forming|near_completion|completed|failed>",
    "market_structure": "trending_up|trending_down|ranging|breakout|breakdown|unclear",
    "trend_description": "<1-2 sentence description of what you see>",
    "key_levels": {{
        "support": [<price1 from chart>, <price2 from chart>],
        "resistance": [<price1 from chart>, <price2 from chart>],
        "current_price_area": "<where price is relative to levels>"
    }},
    "candlestick_notes": "<any significant candle patterns at key levels>",
    "volume_analysis": "<if volume visible, what does it suggest>",
    "bullish_scenarios": [
        {{
            "name": "<scenario based on chart>",
            "probability": <20-60>,
            "trigger": "<what price action triggers this>",
            "target": "<price or description from chart>",
            "explanation": "<reasoning based on what you see>"
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
            "name": "<scenario based on chart>",
            "probability": <20-60>,
            "trigger": "<trigger>",
            "target": "<target>",
            "explanation": "<reasoning>"
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
        "entry": "<price or zone based on chart>",
        "stop_loss": "<price below/above structure>",
        "take_profit_1": "<first target>",
        "take_profit_2": "<second target>",
        "take_profit_3": "<extended target>",
        "risk_reward": <calculated RR ratio>
    }},
    "entry_confirmation": "<what to wait for before entering>",
    "confidence_score": <40-85>,
    "invalidation_conditions": [
        "<what would invalidate this analysis>",
        "<secondary invalidation>"
    ],
    "reasoning": "<4-6 sentence comprehensive analysis of what you see in the chart, the setup quality, key decision points, and risks. Reference specific levels visible in the chart.>"
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
