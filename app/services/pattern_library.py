"""
Institutional Price Action Pattern Library
Based on Quasimodo (QM) and Smart Money Concepts
Used by both Lambda Scanner and Chart AI
"""

INSTITUTIONAL_PATTERNS = """
## QUASIMODO (QM) PATTERNS - High Probability Reversals

### QM Quick Retest (Bearish)
- Structure: Higher High (HH) → Low (L) → Lower High (H) → Lower Low (LL)
- Entry: At QM Level (QML) which is the original Low (L)
- Stop Loss: Above the Lower High (H)
- Target: Equal distance below entry as HH to QML
- Probability: 65-75% when volume confirms

### QM Quick Retest (Bullish)
- Structure: Lower Low (LL) → High (H) → Higher Low (L) → Higher High (HH)
- Entry: At QM Level (QML) which is the original High (H)
- Stop Loss: Below the Higher Low (L)
- Target: Equal distance above entry as LL to QML

### QM Late Retest
- Same structure but retest of QML comes after more price action
- Higher probability due to additional confirmation
- Entry: QML level on delayed retest

### QM Shadow
- Structure: HH with long wick rejection above QML
- The shadow/wick shows institutional selling
- Entry: Below the shadow after bearish confirmation
- Very high probability pattern (70-80%)

### QM Re-Entry
- Failed first entry, price returns to QML again
- Entry at "small QML" or main QML second touch
- Tighter stop loss possible

### Continuation QM
- QM pattern within an existing trend
- Continue Uptrend: Higher Low QM setup
- Continue Downtrend: Lower High QM setup

### Ignored QM (IQM / IQMTR)
- QML level is swept/ignored initially
- Wait for Fakeout and return to QML
- Entry after the sweep and reclaim

## FLAG PATTERNS - Continuation Setups

### Flag B (Bearish)
- Sharp move down (pole) → consolidation (flag)
- Flag Limit = Supply zone at top of flag
- Entry: Rejection from Flag Limit / Supply
- Target: Measured move equal to pole

### Flag A + Flag B
- Double flag structure for higher probability
- Entry after both flags confirm direction

### Bull Flag
- Sharp move up (pole) → consolidation (flag)
- Entry: Break above flag with volume
- Target: Measured move equal to pole

## FAKEOUT PATTERNS - Liquidity Grabs

### Fakeout V1 (Default)
- Price breaks key level (R1/R2 or S1/S2)
- Immediately reverses back inside range
- Entry: After reclaim of broken level
- High probability reversal signal

### Fakeout V2 (SR Flip)
- Support/Resistance flip after fakeout
- SR becomes RS or RS becomes SR
- Entry: On retest of flipped level

### Fakeout V3 (Diamond)
- Diamond shape forms at key level
- Head of QM at same level as previous R1/R2 or S1/S2
- Entry: Break of diamond in direction of fakeout

### Fakeout V4 (Diamond SBR)
- Diamond with Support Becomes Resistance
- More complex but higher probability

## LIQUIDITY PATTERNS

### Stop Hunt / Supply
- Price spikes to take out obvious stops
- Engulfs previous high (stop hunt)
- Entry: After engulfing candle closes
- Stop Loss: Above the stop hunt wick

### Stop Hunt / Demand
- Price spikes down to take out stops
- Engulfs previous low
- Entry: After bullish engulfing confirmation

### MPL (Market Profile Levels)
- Entry at MPL after stop hunt
- Wait for Fakeout confirmation

## COMPRESSION PATTERNS

### Compression (CP1)
- Tightening range with clear demand/supply zones
- Demand Clear or Supply Clear setups
- Entry: Break of compression in trend direction

### Compression Liquidity (CPG2)
- Compression with internal liquidity (IQ)
- R-R levels define the range
- Entry: After IQ sweep and reversal

## OTHER HIGH-PROBABILITY SETUPS

### Double SSR (Support-Support-Resistance)
- Triple touch confirms level strength
- Entry: Third touch with confirmation

### 3 Drive
- Three pushes in same direction
- Each drive gets weaker
- Entry: After third drive exhaustion

### Can-Can
- Multiple tests of same level
- Level holds repeatedly
- Entry: On confirmed bounce

### Can-Can + Fakeout
- Can-Can level gets swept
- Fakeout creates high probability reversal
- Entry: After fakeout reclaim

### V Twin
- Double bottom/top with V shape
- Entry: Break of neckline
- Target: Height of V projected

### Ruler (Remnants)
- Measured moves using previous swings
- 1-2-3 pattern projections
- Target: 2-3 projection levels

## MULTI-TIMEFRAME ANALYSIS

### Confluence Rules:
1. Daily chart sets the bias (trend direction)
2. 12H/8H confirms structure
3. 4H provides entry timing
4. Pattern on higher TF = stronger signal

### Entry Criteria:
- Pattern identified on 4H minimum
- Higher TF supports the direction
- Volume confirms the move
- Risk:Reward minimum 2:1
"""

def get_pattern_prompt():
    """Return the pattern library for AI analysis"""
    return INSTITUTIONAL_PATTERNS

def get_analysis_prompt(symbol: str, timeframe: str, price_data: dict = None):
    """Generate analysis prompt with pattern library"""
    
    prompt = f"""You are an elite institutional trader analyzing {symbol} on the {timeframe} timeframe.

{INSTITUTIONAL_PATTERNS}

## YOUR TASK:
Analyze the current price action for {symbol} and identify:

1. **Primary Pattern**: Which institutional pattern is forming or has formed?
2. **Pattern Stage**: Is it early formation, confirmed, or completing?
3. **Key Levels**:
   - QML / Entry Zone
   - Stop Loss level
   - Target 1 (conservative)
   - Target 2 (full measured move)
4. **Confluence Factors**: What supports this setup?
5. **Invalidation**: What would invalidate this pattern?

## RESPONSE FORMAT (JSON):
{{
    "pattern_detected": "Pattern Name (e.g., QM Quick Retest Bullish)",
    "pattern_stage": "forming|confirmed|completing",
    "confidence": 0-100,
    "bias": "bullish|bearish|neutral",
    "entry_zone": {{"low": price, "high": price}},
    "stop_loss": price,
    "target_1": price,
    "target_2": price,
    "risk_reward": ratio,
    "key_levels": {{
        "qml": price,
        "support": [prices],
        "resistance": [prices]
    }},
    "confluence": ["list of supporting factors"],
    "invalidation": "description of what invalidates",
    "reasoning": "2-3 sentence explanation"
}}

Be selective - only identify patterns with clear structure. If no institutional pattern is present, set confidence below 50.
"""
    return prompt
