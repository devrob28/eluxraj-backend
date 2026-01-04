"""
Trade Intelligence Service V2
Institutional-grade AI-powered trade playbooks and chart analysis
"""
import httpx
import json
import base64
import os
from typing import Dict, Optional, List
from datetime import datetime, timezone, timedelta
from app.core.logging import logger


class TradeIntelligenceService:
    """AI-powered trade analysis and playbook generation"""
    
    ANTHROPIC_API = "https://api.anthropic.com/v1/messages"
    
    def __init__(self):
        """Initialize service"""
        pass
    
    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment or settings"""
        # Try direct environment variable first
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            logger.info(f"Got API key from env (length: {len(api_key)})")
            return api_key
        
        # Try settings
        try:
            from app.core.config import settings
            api_key = getattr(settings, "ANTHROPIC_API_KEY", None)
            if api_key:
                logger.info(f"Got API key from settings (length: {len(api_key)})")
                return api_key
        except Exception as e:
            logger.error(f"Failed to get API key from settings: {e}")
        
        logger.error("No ANTHROPIC_API_KEY found in env or settings")
        return None
    
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
        
        prompt = f"""You are a senior quantitative analyst at a top-tier hedge fund. Analyze {asset} ({asset_type}) on the {timeframe} timeframe.

Current Price: ${current_price:,.2f}
Analysis Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}

Provide a complete trade playbook with entry zones, stop loss, take profit targets, and scenario analysis.

RESPOND WITH VALID JSON ONLY:

{{
    "market_bias": "bullish|bearish|neutral",
    "bias_strength": <50-85>,
    "market_structure": "trending_up|trending_down|ranging|breakout|breakdown",
    "entry_zone": {{
        "low": <price within 3% below current>,
        "high": <price within 2% above current>,
        "rationale": "<reason>"
    }},
    "stop_loss": {{
        "price": <price>,
        "percentage": <2-8>,
        "rationale": "<reason>"
    }},
    "take_profits": [
        {{"level": "TP1", "price": <target1>, "probability": <50-70>, "rationale": "<reason>"}},
        {{"level": "TP2", "price": <target2>, "probability": <30-50>, "rationale": "<reason>"}},
        {{"level": "TP3", "price": <target3>, "probability": <15-35>, "rationale": "<reason>"}}
    ],
    "risk_reward_ratio": <calculated RR>,
    "probability_score": <40-75>,
    "confidence_score": <50-80>,
    "pattern_detected": "<pattern or 'No clear pattern'>",
    "bullish_scenarios": [
        {{"name": "<scenario>", "probability": <20-50>, "trigger": "<trigger>", "target": <price>, "explanation": "<reasoning>"}},
        {{"name": "<scenario2>", "probability": <15-40>, "trigger": "<trigger>", "target": <price>, "explanation": "<reasoning>"}},
        {{"name": "<scenario3>", "probability": <10-30>, "trigger": "<trigger>", "target": <price>, "explanation": "<reasoning>"}}
    ],
    "bearish_scenarios": [
        {{"name": "<scenario>", "probability": <20-50>, "trigger": "<trigger>", "target": <price>, "explanation": "<reasoning>"}},
        {{"name": "<scenario2>", "probability": <15-40>, "trigger": "<trigger>", "target": <price>, "explanation": "<reasoning>"}},
        {{"name": "<scenario3>", "probability": <10-30>, "trigger": "<trigger>", "target": <price>, "explanation": "<reasoning>"}}
    ],
    "invalidation_conditions": ["<condition1>", "<condition2>"],
    "invalidation_price": <price>,
    "reasoning": "<4-6 sentence comprehensive analysis>"
}}"""

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
            return self._fallback_analysis(asset, timeframe)
        
        prompt = f"""Analyze this {asset} chart on the {timeframe} timeframe.

Provide technical analysis with key levels, patterns, and trade recommendations.

RESPOND WITH VALID JSON ONLY:

{{
    "chart_quality": "clear|moderate|poor",
    "trend_direction": "uptrend|downtrend|sideways",
    "pattern_detected": "<pattern name>",
    "market_structure": "trending_up|trending_down|ranging|breakout|breakdown",
    "key_levels": {{
        "support": ["<price1>", "<price2>"],
        "resistance": ["<price1>", "<price2>"]
    }},
    "bullish_scenarios": [
        {{"name": "<scenario>", "probability": <20-60>, "trigger": "<trigger>", "target": "<price>", "explanation": "<reasoning>"}}
    ],
    "bearish_scenarios": [
        {{"name": "<scenario>", "probability": <20-60>, "trigger": "<trigger>", "target": "<price>", "explanation": "<reasoning>"}}
    ],
    "trade_recommendation": "long|short|wait",
    "trade_setup": {{
        "bias": "bullish|bearish|neutral",
        "entry_zone": "<price zone>",
        "stop_loss": "<price>",
        "take_profit_1": "<price>",
        "take_profit_2": "<price>",
        "risk_reward": "<ratio>"
    }},
    "confidence_score": <40-85>,
    "invalidation_conditions": ["<condition>"],
    "reasoning": "<5-7 sentence analysis>"
}}"""

        return await self._call_ai_with_image(prompt, image_data, media_type)
    
    async def _call_ai(self, prompt: str) -> Dict:
        """Call Anthropic API for text analysis"""
        api_key = self._get_api_key()
        if not api_key:
            return self._fallback_playbook()
        
        try:
            logger.info("Making Anthropic API call...")
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
                        "max_tokens": 4096,
                        "messages": [{"role": "user", "content": prompt}]
                    },
                    timeout=90.0
                )
                
                logger.info(f"Anthropic API response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["content"][0]["text"]
                    logger.info(f"Got AI response, length: {len(content)}")
                    return self._parse_json_response(content)
                else:
                    logger.error(f"Anthropic API error: {response.status_code} - {response.text[:500]}")
                    return self._fallback_playbook()
        except httpx.TimeoutException:
            logger.error("Anthropic API timeout")
            return self._fallback_playbook()
        except Exception as e:
            logger.error(f"AI call failed: {type(e).__name__}: {e}")
            return self._fallback_playbook()
    
    async def _call_ai_with_image(self, prompt: str, image_data: str, media_type: str) -> Dict:
        """Call Anthropic API with image"""
        api_key = self._get_api_key()
        if not api_key:
            return self._fallback_analysis("", "")
        
        try:
            logger.info("Making Anthropic API call with image...")
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
                
                logger.info(f"Anthropic API response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["content"][0]["text"]
                    logger.info(f"Got AI response, length: {len(content)}")
                    return self._parse_json_response(content)
                else:
                    logger.error(f"Anthropic API error: {response.status_code} - {response.text[:500]}")
                    return self._fallback_analysis("", "")
        except httpx.TimeoutException:
            logger.error("Anthropic API timeout (image)")
            return self._fallback_analysis("", "")
        except Exception as e:
            logger.error(f"AI image call failed: {type(e).__name__}: {e}")
            return self._fallback_analysis("", "")
    
    def _parse_json_response(self, content: str) -> Dict:
        """Parse JSON from AI response"""
        content = content.strip()
        
        # Remove markdown code blocks
        if content.startswith("```"):
            import re
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
            if match:
                content = match.group(1).strip()
        
        # Try direct parse
        try:
            result = json.loads(content)
            logger.info("Successfully parsed JSON response")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f"Direct JSON parse failed: {e}")
        
        # Find JSON object with brace matching
        try:
            start = content.find("{")
            if start != -1:
                depth = 0
                end = start
                for i, char in enumerate(content[start:], start):
                    if char == "{":
                        depth += 1
                    elif char == "}":
                        depth -= 1
                        if depth == 0:
                            end = i + 1
                            break
                json_str = content[start:end]
                result = json.loads(json_str)
                logger.info("Successfully parsed extracted JSON")
                return result
        except json.JSONDecodeError as e:
            logger.error(f"Extracted JSON parse failed: {e}")
        
        logger.error(f"All JSON parsing attempts failed")
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
