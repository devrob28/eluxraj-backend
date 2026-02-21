"""
Chart Analysis Service - AI-powered chart pattern recognition
Uses institutional price action patterns for analysis
"""
import anthropic
import base64
import json
import re
from typing import Optional, Dict
from app.core.config import settings
from app.core.logging import logger
from app.services.pattern_library import INSTITUTIONAL_PATTERNS


class ChartAnalysisService:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    async def analyze_chart(self, image_data: str, asset: str = "Unknown", timeframe: str = "Unknown") -> Dict:
        """Analyze a chart image using AI with institutional pattern recognition"""
        
        logger.info(f"Analyzing chart for {asset} ({timeframe})")
        
        prompt = f"""You are an elite institutional trader with expertise in Smart Money Concepts and Quasimodo (QM) patterns.

{INSTITUTIONAL_PATTERNS}

## CHART ANALYSIS TASK

Analyze this {asset} chart on the {timeframe} timeframe.

### Step 1: Identify Market Structure
- Current trend (bullish/bearish/ranging)
- Key swing highs and lows
- Break of Structure (BOS) or Change of Character (ChoCH)

### Step 2: Identify Institutional Patterns
Look for these specific patterns:
- Quasimodo (QM) setups - Quick Retest, Late Retest, Shadow, Re-Entry
- Flag patterns - Bull Flag, Bear Flag, Flag A+B
- Fakeout patterns - V1, V2 (SR Flip), V3 (Diamond)
- Liquidity patterns - Stop Hunt, MPL
- Compression patterns
- Can-Can setups

### Step 3: Define Trade Setup
If a valid pattern exists, provide:
- Exact entry zone
- Stop loss level
- Target 1 and Target 2
- Risk:Reward ratio

### Step 4: Multi-Timeframe Context
- How does this timeframe fit with higher timeframes?
- Is there confluence?

## RESPONSE FORMAT (JSON only, no other text):
{{
    "market_structure": {{
        "trend": "bullish|bearish|ranging",
        "last_bos": "description of last break of structure",
        "key_swing_high": "price or 'visible at X level'",
        "key_swing_low": "price or 'visible at X level'"
    }},
    "pattern_detected": "Specific pattern name from the library above",
    "pattern_stage": "forming|confirmed|completing|none",
    "confidence_score": 0-100,
    "trade_recommendation": "BUY|SELL|WAIT",
    "trade_setup": {{
        "bias": "bullish|bearish|neutral",
        "entry_zone": {{"low": "price", "high": "price"}},
        "stop_loss": "price",
        "target_1": "price",
        "target_2": "price",
        "risk_reward": "ratio like 2.5"
    }},
    "key_levels": {{
        "qml_level": "price if applicable",
        "support_levels": ["price1", "price2"],
        "resistance_levels": ["price1", "price2"],
        "liquidity_zones": ["description of where stops likely are"]
    }},
    "confluence_factors": [
        "list of factors supporting this trade"
    ],
    "invalidation": "What price action would invalidate this setup",
    "reasoning": "3-4 sentence explanation of the analysis using institutional terminology"
}}

IMPORTANT: 
- Use the exact pattern names from the library
- Be specific about price levels visible on the chart
- Only recommend trades with minimum 2:1 R:R
- If no clear institutional pattern, set confidence below 50 and recommendation to WAIT
"""

        try:
            # Handle base64 image
            if image_data.startswith('data:'):
                image_data = image_data.split(',')[1]
            
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_data
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            response_text = message.content[0].text
            logger.info(f"Raw AI response length: {len(response_text)}")
            
            # Parse JSON from response
            result = self._parse_json_response(response_text)
            
            if result:
                result['asset'] = asset
                result['timeframe'] = timeframe
                result['analysis_type'] = 'institutional_patterns'
                return result
            else:
                return self._get_fallback_response(asset, timeframe)
                
        except Exception as e:
            logger.error(f"Chart analysis error: {e}")
            return self._get_fallback_response(asset, timeframe)
    
    def _parse_json_response(self, content: str) -> Optional[Dict]:
        """Parse JSON from AI response with multiple fallback strategies"""
        try:
            # Strategy 1: Direct parse
            return json.loads(content)
        except:
            pass
        
        try:
            # Strategy 2: Extract JSON from markdown code blocks
            if "```" in content:
                match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
                if match:
                    return json.loads(match.group(1))
        except:
            pass
        
        try:
            # Strategy 3: Find JSON by braces
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end > start:
                json_str = content[start:end]
                return json.loads(json_str)
        except:
            pass
        
        try:
            # Strategy 4: Fix common JSON issues
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end > start:
                json_str = content[start:end]
                # Remove trailing commas
                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                return json.loads(json_str)
        except:
            pass
        
        logger.warning("Could not parse JSON from response")
        return None
    
    def _get_fallback_response(self, asset: str, timeframe: str) -> Dict:
        """Return a fallback response when analysis fails"""
        return {
            "asset": asset,
            "timeframe": timeframe,
            "market_structure": {
                "trend": "unknown",
                "last_bos": "Unable to determine",
                "key_swing_high": "N/A",
                "key_swing_low": "N/A"
            },
            "pattern_detected": "None identified",
            "pattern_stage": "none",
            "confidence_score": 0,
            "trade_recommendation": "WAIT",
            "trade_setup": {
                "bias": "neutral",
                "entry_zone": {"low": "N/A", "high": "N/A"},
                "stop_loss": "N/A",
                "target_1": "N/A",
                "target_2": "N/A",
                "risk_reward": "N/A"
            },
            "key_levels": {
                "qml_level": "N/A",
                "support_levels": [],
                "resistance_levels": [],
                "liquidity_zones": []
            },
            "confluence_factors": [],
            "invalidation": "N/A",
            "reasoning": "Unable to analyze the chart. Please ensure the image is clear and shows price action with candlesticks.",
            "analysis_type": "fallback"
        }


# Singleton instance
chart_analysis_service = ChartAnalysisService()
