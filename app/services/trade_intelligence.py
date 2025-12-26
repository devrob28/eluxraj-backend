"""
Trade Intelligence Service
Generates AI-powered trade playbooks and chart analysis
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
        
        prompt = f"""You are an elite quantitative analyst providing institutional-grade trade intelligence.

ASSET: {asset}
TYPE: {asset_type}
TIMEFRAME: {timeframe}
CURRENT PRICE: ${current_price:,.2f}
MARKET DATA: {json.dumps(market_data) if market_data else 'Not provided'}

Generate a complete TRADE PLAYBOOK with the following structure. Be precise with numbers.

IMPORTANT RULES:
1. All probabilities must sum appropriately
2. Include uncertainty - never guarantee outcomes
3. Provide clear invalidation logic
4. Risk-reward must be calculated accurately
5. This is decision intelligence, NOT financial advice

Respond ONLY with valid JSON in this exact format:
{{
    "market_bias": "bullish|bearish|neutral",
    "bias_strength": <0-100>,
    "entry_zone": {{
        "low": <price>,
        "high": <price>,
        "rationale": "<why this zone>"
    }},
    "stop_loss": {{
        "price": <price>,
        "percentage": <% from entry>,
        "rationale": "<why here>"
    }},
    "take_profits": [
        {{"level": "TP1", "price": <price>, "probability": <0-100>, "rationale": "<reason>"}},
        {{"level": "TP2", "price": <price>, "probability": <0-100>, "rationale": "<reason>"}},
        {{"level": "TP3", "price": <price>, "probability": <0-100>, "rationale": "<reason>"}}
    ],
    "risk_reward_ratio": <number>,
    "probability_score": <0-100>,
    "confidence_score": <0-100>,
    "bullish_scenarios": [
        {{"name": "<scenario name>", "probability": <0-100>, "trigger": "<what causes this>", "target": <price>, "explanation": "<detailed reasoning>"}},
        {{"name": "<scenario name>", "probability": <0-100>, "trigger": "<what causes this>", "target": <price>, "explanation": "<detailed reasoning>"}},
        {{"name": "<scenario name>", "probability": <0-100>, "trigger": "<what causes this>", "target": <price>, "explanation": "<detailed reasoning>"}}
    ],
    "bearish_scenarios": [
        {{"name": "<scenario name>", "probability": <0-100>, "trigger": "<what causes this>", "target": <price>, "explanation": "<detailed reasoning>"}},
        {{"name": "<scenario name>", "probability": <0-100>, "trigger": "<what causes this>", "target": <price>, "explanation": "<detailed reasoning>"}},
        {{"name": "<scenario name>", "probability": <0-100>, "trigger": "<what causes this>", "target": <price>, "explanation": "<detailed reasoning>"}}
    ],
    "invalidation_conditions": [
        "<condition 1>",
        "<condition 2>",
        "<condition 3>"
    ],
    "invalidation_price": <price where thesis is invalid>,
    "pattern_detected": "<technical pattern if any>",
    "market_structure": "trending_up|trending_down|ranging|breakout|breakdown",
    "reasoning": "<comprehensive analysis reasoning>"
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
        
        prompt = f"""You are an elite technical analyst with 20+ years of experience. Analyze this chart image.

ASSET: {asset}
TIMEFRAME: {timeframe}

Provide institutional-grade analysis. Be specific with price levels visible in the chart.

IMPORTANT RULES:
1. If the chart is unclear or you cannot identify patterns, say "no_trade" 
2. Include uncertainty in all probability assessments
3. Never guarantee outcomes
4. Provide clear invalidation logic
5. This is decision intelligence, NOT financial advice

Respond ONLY with valid JSON:
{{
    "pattern_detected": "<pattern name or 'none'>",
    "market_structure": "trending_up|trending_down|ranging|breakout|breakdown|unclear",
    "key_levels": {{
        "support": [<price1>, <price2>],
        "resistance": [<price1>, <price2>]
    }},
    "bullish_scenarios": [
        {{"name": "<scenario>", "probability": <0-100>, "trigger": "<condition>", "target": "<price or description>", "explanation": "<reasoning>"}},
        {{"name": "<scenario>", "probability": <0-100>, "trigger": "<condition>", "target": "<price or description>", "explanation": "<reasoning>"}},
        {{"name": "<scenario>", "probability": <0-100>, "trigger": "<condition>", "target": "<price or description>", "explanation": "<reasoning>"}}
    ],
    "bearish_scenarios": [
        {{"name": "<scenario>", "probability": <0-100>, "trigger": "<condition>", "target": "<price or description>", "explanation": "<reasoning>"}},
        {{"name": "<scenario>", "probability": <0-100>, "trigger": "<condition>", "target": "<price or description>", "explanation": "<reasoning>"}},
        {{"name": "<scenario>", "probability": <0-100>, "trigger": "<condition>", "target": "<price or description>", "explanation": "<reasoning>"}}
    ],
    "trade_recommendation": "long|short|no_trade|wait",
    "trade_setup": {{
        "entry": "<price or zone>",
        "stop_loss": "<price>",
        "take_profit_1": "<price>",
        "take_profit_2": "<price>",
        "take_profit_3": "<price>",
        "risk_reward": <ratio>
    }},
    "confidence_score": <0-100>,
    "invalidation_conditions": ["<condition1>", "<condition2>"],
    "reasoning": "<comprehensive analysis>"
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
                        "model": "claude-3-5-sonnet-20241022",
                        "max_tokens": 4096,
                        "messages": [{"role": "user", "content": prompt}]
                    },
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["content"][0]["text"]
                    # Extract JSON from response
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
                        "model": "claude-3-5-sonnet-20241022",
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
                    timeout=90.0
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
        logger.error(f"Failed to parse AI response: {content[:200]}")
        return self._fallback_playbook()
    
    def _fallback_playbook(self) -> Dict:
        """Return fallback when AI unavailable"""
        return {
            "market_bias": "neutral",
            "bias_strength": 50,
            "entry_zone": {"low": 0, "high": 0, "rationale": "Analysis unavailable"},
            "stop_loss": {"price": 0, "percentage": 5, "rationale": "Default 5%"},
            "take_profits": [
                {"level": "TP1", "price": 0, "probability": 33, "rationale": "Pending"},
                {"level": "TP2", "price": 0, "probability": 33, "rationale": "Pending"},
                {"level": "TP3", "price": 0, "probability": 33, "rationale": "Pending"}
            ],
            "risk_reward_ratio": 0,
            "probability_score": 50,
            "confidence_score": 0,
            "bullish_scenarios": [{"name": "Pending Analysis", "probability": 33, "trigger": "N/A", "target": 0, "explanation": "AI analysis unavailable"}],
            "bearish_scenarios": [{"name": "Pending Analysis", "probability": 33, "trigger": "N/A", "target": 0, "explanation": "AI analysis unavailable"}],
            "invalidation_conditions": ["Analysis unavailable"],
            "invalidation_price": 0,
            "pattern_detected": "none",
            "market_structure": "unclear",
            "reasoning": "AI analysis temporarily unavailable. Please try again.",
            "error": True
        }
    
    def _fallback_analysis(self, asset: str, timeframe: str) -> Dict:
        """Return fallback for chart analysis"""
        return {
            "pattern_detected": "none",
            "market_structure": "unclear",
            "key_levels": {"support": [], "resistance": []},
            "bullish_scenarios": [{"name": "Analysis Pending", "probability": 33, "trigger": "N/A", "target": "N/A", "explanation": "Unable to process chart"}],
            "bearish_scenarios": [{"name": "Analysis Pending", "probability": 33, "trigger": "N/A", "target": "N/A", "explanation": "Unable to process chart"}],
            "trade_recommendation": "no_trade",
            "trade_setup": None,
            "confidence_score": 0,
            "invalidation_conditions": ["Analysis unavailable"],
            "reasoning": "Chart analysis temporarily unavailable.",
            "error": True
        }


trade_intelligence = TradeIntelligenceService()
