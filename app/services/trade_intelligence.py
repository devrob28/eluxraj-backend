"""
Trade Intelligence Service V2 - Production Ready
Institutional-grade AI-powered trade playbooks and chart analysis
"""
import httpx
import json
import os
import re
import base64
from typing import Dict, Optional
from datetime import datetime, timezone
from app.core.logging import logger


class TradeIntelligenceService:
    """AI-powered trade analysis and playbook generation"""
    
    ANTHROPIC_API = "https://api.anthropic.com/v1/messages"
    
    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment"""
        return os.getenv("ANTHROPIC_API_KEY")
    
    async def generate_playbook(
        self,
        asset: str,
        asset_type: str,
        timeframe: str,
        current_price: float,
        market_data: Dict = None
    ) -> Dict:
        """Generate a complete trade playbook"""
        
        prompt = f"""You are a senior quantitative analyst. Analyze {asset} ({asset_type}) on the {timeframe} timeframe.
Current Price: ${current_price:,.2f}
Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}

Provide a trade playbook. Return ONLY valid JSON, no markdown code blocks, no extra text.

The JSON must have this exact structure:
{{
    "market_bias": "bullish",
    "bias_strength": 68,
    "market_structure": "trending_up",
    "entry_zone": {{
        "low": {round(current_price * 0.97, 2)},
        "high": {round(current_price * 1.01, 2)},
        "rationale": "Key support zone with buyer interest"
    }},
    "stop_loss": {{
        "price": {round(current_price * 0.94, 2)},
        "percentage": 6,
        "rationale": "Below major support structure"
    }},
    "take_profits": [
        {{"level": "TP1", "price": {round(current_price * 1.05, 2)}, "probability": 65, "rationale": "Near resistance"}},
        {{"level": "TP2", "price": {round(current_price * 1.10, 2)}, "probability": 45, "rationale": "Major resistance"}},
        {{"level": "TP3", "price": {round(current_price * 1.18, 2)}, "probability": 25, "rationale": "Extended target"}}
    ],
    "risk_reward_ratio": 2.5,
    "probability_score": 62,
    "confidence_score": 70,
    "pattern_detected": "Higher lows forming",
    "bullish_scenarios": [
        {{"name": "Breakout Rally", "probability": 40, "trigger": "Break above resistance", "target": {round(current_price * 1.12, 2)}, "explanation": "Momentum continuation if key level breaks"}},
        {{"name": "Support Bounce", "probability": 35, "trigger": "Hold support zone", "target": {round(current_price * 1.08, 2)}, "explanation": "Buyers defend key level"}},
        {{"name": "Accumulation Break", "probability": 20, "trigger": "Volume spike", "target": {round(current_price * 1.15, 2)}, "explanation": "Institutional accumulation completes"}}
    ],
    "bearish_scenarios": [
        {{"name": "Support Breakdown", "probability": 25, "trigger": "Break below support", "target": {round(current_price * 0.92, 2)}, "explanation": "Sellers overwhelm buyers"}},
        {{"name": "Lower High Rejection", "probability": 20, "trigger": "Fail at resistance", "target": {round(current_price * 0.95, 2)}, "explanation": "Trend reversal signal"}},
        {{"name": "Momentum Fade", "probability": 15, "trigger": "Volume decline", "target": {round(current_price * 0.90, 2)}, "explanation": "Buying pressure exhausted"}}
    ],
    "invalidation_conditions": ["Close below ${round(current_price * 0.93, 2)}", "Break of market structure"],
    "invalidation_price": {round(current_price * 0.93, 2)},
    "reasoning": "Price is showing strength with higher lows. Key support holding well. Watch for breakout above resistance for continuation. Risk management essential with stop below structure."
}}

Now analyze {asset} at ${current_price:,.2f} and provide YOUR analysis with realistic values based on current market conditions. Return only the JSON object."""

        return await self._call_ai(prompt)
    
    async def analyze_chart_image(
        self,
        image_path: str,
        asset: str,
        timeframe: str
    ) -> Dict:
        """Analyze a chart image and return trade intelligence"""
        
        try:
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            media_type = "image/png" if image_path.lower().endswith(".png") else "image/jpeg"
        except Exception as e:
            logger.error(f"Failed to read image: {e}")
            return self._fallback_analysis()
        
        prompt = f"""You are an elite institutional trader analyzing this {asset} chart on the {timeframe} timeframe.

## INSTITUTIONAL PATTERNS TO IDENTIFY:

### QUASIMODO (QM) PATTERNS - High Probability Reversals
- QM Quick Retest: HH → L → Lower H → LL, entry at QML (original Low)
- QM Late Retest: Same but delayed retest of QML
- QM Shadow: HH with wick rejection above QML
- QM Re-Entry: Failed first entry, price returns to QML
- Continuation QM: QM within existing trend

### FLAG PATTERNS - Continuation
- Bull Flag: Sharp up → consolidation → break higher
- Bear Flag: Sharp down → consolidation → break lower
- Flag A+B: Double flag structure

### FAKEOUT PATTERNS - Liquidity Grabs
- Fakeout V1: Break key level → immediate reversal
- Fakeout V2 (SR Flip): Support becomes Resistance or vice versa
- Fakeout V3 (Diamond): Diamond shape at key level

### LIQUIDITY PATTERNS
- Stop Hunt / Supply: Spike above to grab stops → reversal
- Stop Hunt / Demand: Spike below to grab stops → reversal

### OTHER SETUPS
- Compression: Tightening range before explosive move
- Double SSR: Triple touch confirmation
- 3 Drive: Three weakening pushes
- Can-Can: Multiple tests of same level

## YOUR TASK:
1. Identify the market structure (trend, BOS, ChoCH)
2. Look for any institutional pattern from the list above
3. Define precise entry, stop loss, and targets
4. Calculate risk:reward ratio

Return ONLY valid JSON with this structure:
{{
    "market_structure": {{
        "trend": "bullish/bearish/ranging",
        "last_bos": "break of structure description",
        "key_swing_high": "price level",
        "key_swing_low": "price level"
    }},
    "pattern_detected": "Specific pattern name from list above",
    "pattern_stage": "forming/confirmed/completing",
    "key_levels": {{
        "qml_level": "price if applicable",
        "support": ["price1", "price2"],
        "resistance": ["price1", "price2"],
        "liquidity_zones": ["where stops likely are"]
    }},
    "bullish_scenarios": [
        {{"name": "Scenario name", "probability": 45, "trigger": "What triggers it", "target": "price", "explanation": "Why"}}
    ],
    "bearish_scenarios": [
        {{"name": "Scenario name", "probability": 30, "trigger": "What triggers it", "target": "price", "explanation": "Why"}}
    ],
    "trade_recommendation": "BUY/SELL/WAIT",
    "trade_setup": {{
        "bias": "bullish/bearish/neutral",
        "entry_zone": {{"low": "price", "high": "price"}},
        "stop_loss": "price",
        "take_profit_1": "price",
        "take_profit_2": "price",
        "risk_reward": "ratio"
    }},
    "confidence_score": 0-100,
    "invalidation_conditions": ["what invalidates this setup"],
    "reasoning": "3-5 sentence institutional analysis explaining the pattern, why it's valid, and the trade logic."
}}

## MOMENTUM & TREND FOLLOWING INDICATORS

### MACD Indicator
- ENTRY (Long): When MACD line crosses ABOVE the Signal Line (bullish crossover)
- EXIT (Long): When MACD line crosses BELOW the Signal Line (bearish crossover)
- Histogram: Green/increasing = bullish momentum, Red/decreasing = bearish

### RSI Indicator (Relative Strength Index)
- ENTRY (Long): When RSI crosses ABOVE 30 (oversold recovery)
- EXIT (Long): When RSI crosses BELOW 70 (overbought reversal)
- Key levels: 30 (oversold), 50 (neutral), 70 (overbought)

### Supertrend Indicator
- ENTRY (Long): When Supertrend turns GREEN (bullish trend)
- EXIT (Long): When Supertrend turns RED (trend reversal)
- Very reliable for trend following

### Parabolic SAR (Stop and Reverse)
- ENTRY (Long): When price moves ABOVE SAR dots (dots below candles)
- EXIT (Long): When price moves BELOW SAR dots (dots above candles)
- Great for trailing stops and trend direction

## ELLIOTT WAVE THEORY

### Impulse Waves (5-Wave Pattern)
- Wave 1: Initial breakout move, often weak
- Wave 2: Retracement (50-61.8% of Wave 1), NEVER beyond Wave 1 start
- Wave 3: STRONGEST wave, usually 1.618x Wave 1, never the shortest
- Wave 4: Consolidation (38.2% retrace), should not overlap Wave 1 territory
- Wave 5: Final push, often shows divergence, typically equals Wave 1

### Corrective Waves (ABC Pattern)
- Wave A: Initial correction against trend
- Wave B: Counter-trend bounce (often a bull/bear trap)
- Wave C: Final correction leg, typically equals Wave A

### Elliott Wave Entry Rules
- BUY: End of Wave 2 (38.2-61.8% retrace of Wave 1)
- BUY: End of Wave 4 (38.2% retrace of Wave 3)
- BUY: End of Wave C (correction complete)
- SELL/TARGET: End of Wave 3 (1.618x extension) or Wave 5

### Wave 3 Extension Targets
- 1.618x Wave 1 (most common)
- 2.618x Wave 1 (strong momentum)
- 4.236x Wave 1 (extreme extension)

## HARMONIC TRADING PATTERNS

### Gartley Pattern (78.6% Retracement)
- XA: Initial impulse move
- AB: 61.8% retracement of XA
- BC: 38.2-88.6% retracement of AB
- CD: 127.2-161.8% extension of BC
- D point: 78.6% retracement of XA (ENTRY ZONE)
- Stop: Beyond X | Target: 38.2% and 61.8% of AD

### Butterfly Pattern (127% Extension)
- AB: 78.6% retracement of XA
- BC: 38.2-88.6% retracement of AB
- CD: 161.8-261.8% extension of BC
- D point: 127.2-161.8% EXTENSION of XA (beyond X)
- Larger reversal potential than Gartley

### Bat Pattern (88.6% Retracement)
- AB: 38.2-50% retracement of XA
- BC: 38.2-88.6% retracement of AB
- CD: 161.8-261.8% extension of BC
- D point: 88.6% retracement of XA (ENTRY ZONE)
- Tightest stop loss of all harmonics

### Crab Pattern (161.8% Extension)
- AB: 38.2-61.8% retracement of XA
- BC: 38.2-88.6% retracement of AB
- CD: 261.8-361.8% extension of BC
- D point: 161.8% extension of XA
- Highest risk/reward harmonic

### Cypher Pattern (78.6% of XC)
- AB: 38.2-61.8% retracement of XA
- BC: 113-141.4% extension of AB (goes beyond A)
- D point: 78.6% retracement of XC
- Modern pattern with high accuracy

### ABCD Pattern (Simplest Harmonic)
- AB: Initial leg
- BC: 61.8-78.6% retracement of AB
- CD: 127.2-161.8% extension of BC (or CD = AB)
- ENTRY: When CD equals AB length or hits extension
- Best pattern for beginners

### Harmonic Trading Rules
1. Wait for D point completion (PRZ - Potential Reversal Zone)
2. Look for RSI/MACD divergence at D point
3. Stop loss just beyond X (Gartley/Bat) or D extreme
4. Target 1: 38.2% of AD | Target 2: 61.8% of AD
5. Works best in ranging markets

IMPORTANT: Only identify patterns you can clearly see. If no institutional pattern is present, set confidence below 50 and recommendation to WAIT."""

        return await self._call_ai_with_image(prompt, image_data, media_type)
    
    async def _call_ai(self, prompt: str) -> Dict:
        """Call Anthropic API for text analysis"""
        api_key = self._get_api_key()
        if not api_key:
            logger.error("No API key found")
            return self._fallback_playbook()
        
        try:
            logger.info("Calling Anthropic API...")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.ANTHROPIC_API,
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 2000,
                        "messages": [{"role": "user", "content": prompt}]
                    },
                    timeout=60.0
                )
                
                logger.info(f"API status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["content"][0]["text"]
                    logger.info(f"Got response, length: {len(content)}")
                    return self._parse_json_response(content)
                else:
                    logger.error(f"API error: {response.status_code} - {response.text[:200]}")
                    return self._fallback_playbook()
                    
        except httpx.TimeoutException:
            logger.error("API timeout")
            return self._fallback_playbook()
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return self._fallback_playbook()
    
    async def _call_ai_with_image(self, prompt: str, image_data: str, media_type: str) -> Dict:
        """Call Anthropic API with image"""
        api_key = self._get_api_key()
        if not api_key:
            logger.error("No API key found")
            return self._fallback_analysis()
        
        try:
            logger.info("Calling Anthropic API with image...")
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.ANTHROPIC_API,
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 2000,
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
                    timeout=90.0
                )
                
                logger.info(f"API status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["content"][0]["text"]
                    logger.info(f"Got response, length: {len(content)}")
                    return self._parse_json_response(content)
                else:
                    logger.error(f"API error: {response.status_code} - {response.text[:200]}")
                    return self._fallback_analysis()
                    
        except httpx.TimeoutException:
            logger.error("API timeout (image)")
            return self._fallback_analysis()
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return self._fallback_analysis()
    
    def _parse_json_response(self, content: str) -> Dict:
        """Parse JSON from AI response with multiple fallback strategies"""
        content = content.strip()
        
        # Remove markdown code blocks if present
        if "```" in content:
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
            if match:
                content = match.group(1).strip()
        
        # Strategy 1: Direct parse
        try:
            result = json.loads(content)
            logger.info("JSON parsed successfully (direct)")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"Direct parse failed: {e}")
        
        # Strategy 2: Find JSON object with brace matching
        try:
            start = content.find("{")
            if start != -1:
                depth = 0
                end = start
                in_string = False
                escape_next = False
                
                for i, char in enumerate(content[start:], start):
                    if escape_next:
                        escape_next = False
                        continue
                    if char == '\\':
                        escape_next = True
                        continue
                    if char == '"' and not escape_next:
                        in_string = not in_string
                        continue
                    if in_string:
                        continue
                    if char == '{':
                        depth += 1
                    elif char == '}':
                        depth -= 1
                        if depth == 0:
                            end = i + 1
                            break
                
                if depth == 0 and end > start:
                    json_str = content[start:end]
                    result = json.loads(json_str)
                    logger.info("JSON parsed successfully (extracted)")
                    return result
        except json.JSONDecodeError as e:
            logger.warning(f"Extracted parse failed: {e}")
        except Exception as e:
            logger.warning(f"Extraction error: {e}")
        
        # Strategy 3: Try to fix common JSON issues
        try:
            # Remove any trailing commas before } or ]
            fixed = re.sub(r',\s*([}\]])', r'\1', content)
            # Find JSON again
            start = fixed.find("{")
            end = fixed.rfind("}") + 1
            if start != -1 and end > start:
                result = json.loads(fixed[start:end])
                logger.info("JSON parsed successfully (fixed)")
                return result
        except:
            pass
        
        logger.error(f"All JSON parsing failed. Content preview: {content[:300]}...")
        return self._fallback_playbook()
    
    def _fallback_playbook(self) -> Dict:
        """Return fallback when AI unavailable"""
        return {
            "market_bias": "neutral",
            "bias_strength": 50,
            "market_structure": "unclear",
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
            "pattern_detected": "Pending",
            "bullish_scenarios": [{"name": "Analysis Pending", "probability": 33, "trigger": "N/A", "target": 0, "explanation": "AI analysis temporarily unavailable."}],
            "bearish_scenarios": [{"name": "Analysis Pending", "probability": 33, "trigger": "N/A", "target": 0, "explanation": "AI analysis temporarily unavailable."}],
            "invalidation_conditions": ["Analysis unavailable - please retry"],
            "invalidation_price": 0,
            "reasoning": "AI analysis temporarily unavailable. Please try again in a few moments.",
            "error": True
        }
    
    def _fallback_analysis(self) -> Dict:
        """Return fallback for chart analysis"""
        return {
            "chart_quality": "unknown",
            "trend_direction": "unclear",
            "pattern_detected": "Analysis pending",
            "market_structure": "unclear",
            "key_levels": {"support": [], "resistance": []},
            "bullish_scenarios": [{"name": "Pending", "probability": 33, "trigger": "N/A", "target": "N/A", "explanation": "AI analysis temporarily unavailable"}],
            "bearish_scenarios": [{"name": "Pending", "probability": 33, "trigger": "N/A", "target": "N/A", "explanation": "AI analysis temporarily unavailable"}],
            "trade_recommendation": "wait",
            "trade_setup": {
                "bias": "neutral",
                "entry_zone": "N/A",
                "stop_loss": "N/A",
                "take_profit_1": "N/A",
                "take_profit_2": "N/A",
                "risk_reward": "0"
            },
            "confidence_score": 0,
            "invalidation_conditions": ["Analysis unavailable"],
            "reasoning": "AI analysis temporarily unavailable. Please try again.",
            "error": True
        }


# Singleton instance
trade_intelligence = TradeIntelligenceService()
