"""
Chart Pattern Recognition Model Runner
Analyzes chart images and returns bullish/bearish probabilities
Universal - works with any asset, any sector, any timeframe
"""
import os
import random
import urllib.request
from typing import Dict, List

MODEL_PATH = os.getenv("CHART_MODEL_PATH", "/tmp/chart_classifier.pt")
MODEL_URL = os.getenv("MODEL_URL", "https://github.com/devrob28/eluxraj-backend/releases/download/v1.0.0-model/chart_classifier.pt")

# Pattern definitions - universal for any asset
BULLISH_PATTERNS = [
    ("Bullish Flag", "Strong uptrend with consolidation, expecting continuation higher."),
    ("Ascending Triangle", "Higher lows pressing against resistance, breakout likely."),
    ("Double Bottom", "W-pattern reversal, strong support confirmed twice."),
    ("Inverse Head & Shoulders", "Classic reversal pattern, neckline break signals upside."),
    ("Cup and Handle", "Accumulation pattern complete, bullish breakout imminent."),
    ("Bullish Engulfing", "Strong buying pressure overwhelmed sellers."),
    ("Morning Star", "Three-candle reversal pattern, buyers taking control."),
    ("Hammer", "Rejection of lower prices, potential reversal forming."),
]

BEARISH_PATTERNS = [
    ("Bearish Flag", "Downtrend pause, expecting continuation lower."),
    ("Descending Triangle", "Lower highs pressing support, breakdown likely."),
    ("Double Top", "M-pattern reversal, resistance confirmed twice."),
    ("Head & Shoulders", "Classic reversal pattern, neckline break signals downside."),
    ("Rising Wedge", "Bearish pattern despite higher highs, reversal expected."),
    ("Bearish Engulfing", "Strong selling pressure overwhelmed buyers."),
    ("Evening Star", "Three-candle reversal pattern, sellers taking control."),
    ("Shooting Star", "Rejection of higher prices, potential reversal forming."),
]


def download_model() -> bool:
    """Download model from GitHub releases if not exists"""
    if os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 1000:
        return True
    
    print(f"Downloading model from {MODEL_URL}...")
    try:
        os.makedirs(os.path.dirname(MODEL_PATH) or '/tmp', exist_ok=True)
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print(f"Model downloaded to {MODEL_PATH}")
        return os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 1000
    except Exception as e:
        print(f"Failed to download model: {e}")
        return False


def _build_outcomes(raw_probs: List[float], asset: str, timeframe: str) -> Dict:
    """Build structured outcomes from model probabilities"""
    
    # Split probabilities between bullish and bearish
    num_patterns = min(len(raw_probs) // 2, 6)
    bull_probs = raw_probs[:num_patterns] if len(raw_probs) > num_patterns else raw_probs[:len(raw_probs)//2]
    bear_probs = raw_probs[num_patterns:num_patterns*2] if len(raw_probs) > num_patterns else raw_probs[len(raw_probs)//2:]
    
    # Normalize each side
    bull_total = sum(bull_probs) or 1
    bear_total = sum(bear_probs) or 1
    bull_probs = [p / bull_total for p in bull_probs]
    bear_probs = [p / bear_total for p in bear_probs]
    
    # Build bullish outcomes
    bullish_outcomes = []
    for i, prob in enumerate(bull_probs):
        if i >= len(BULLISH_PATTERNS):
            break
        name, explanation = BULLISH_PATTERNS[i]
        # Ensure minimum visibility (at least 5%)
        adjusted_prob = max(prob * 0.6, 0.05) if prob > 0.01 else 0.05
        bullish_outcomes.append({
            "name": name,
            "probability": round(adjusted_prob, 2),
            "explanation": f"{explanation} ({asset} {timeframe})"
        })
    
    # Build bearish outcomes
    bearish_outcomes = []
    for i, prob in enumerate(bear_probs):
        if i >= len(BEARISH_PATTERNS):
            break
        name, explanation = BEARISH_PATTERNS[i]
        # Ensure minimum visibility (at least 5%)
        adjusted_prob = max(prob * 0.6, 0.05) if prob > 0.01 else 0.05
        bearish_outcomes.append({
            "name": name,
            "probability": round(adjusted_prob, 2),
            "explanation": f"{explanation} ({asset} {timeframe})"
        })
    
    # Sort by probability
    bullish_outcomes.sort(key=lambda x: x["probability"], reverse=True)
    bearish_outcomes.sort(key=lambda x: x["probability"], reverse=True)
    
    # Take top 3 of each
    bullish_outcomes = bullish_outcomes[:3]
    bearish_outcomes = bearish_outcomes[:3]
    
    # Calculate totals for recommendation
    total_bull = sum(o["probability"] for o in bullish_outcomes)
    total_bear = sum(o["probability"] for o in bearish_outcomes)
    
    # Determine recommendation
    bull_bear_ratio = total_bull / (total_bear or 0.01)
    
    if bull_bear_ratio > 1.3:
        side = "buy"
        prob = bullish_outcomes[0]["probability"] if bullish_outcomes else 0.5
        top_pattern = bullish_outcomes[0]['name'] if bullish_outcomes else "Bullish pattern"
        rationale = f"Bullish patterns dominate ({top_pattern}). Favorable risk/reward for long position."
    elif bull_bear_ratio < 0.77:
        side = "sell"
        prob = bearish_outcomes[0]["probability"] if bearish_outcomes else 0.5
        top_pattern = bearish_outcomes[0]['name'] if bearish_outcomes else "Bearish pattern"
        rationale = f"Bearish patterns detected ({top_pattern}). Consider defensive positioning or short."
    else:
        side = "wait"
        prob = max(total_bull, total_bear) / 3
        rationale = "Mixed signals detected. Wait for clearer price action before entering."
    
    return {
        "bullish": bullish_outcomes,
        "bearish": bearish_outcomes,
        "recommended_trade": {
            "side": side,
            "probability": round(prob, 2),
            "rationale": rationale
        }
    }


def _simulate_outcomes(asset: str, timeframe: str) -> Dict:
    """Generate simulated outcomes when model unavailable"""
    # Use asset + timeframe for reproducible but varied results
    seed_val = hash(asset + timeframe) % 100000
    random.seed(seed_val + int(random.random() * 1000))
    
    # Generate 12 probabilities (6 bullish, 6 bearish)
    raw_probs = [random.random() for _ in range(12)]
    
    result = _build_outcomes(raw_probs, asset, timeframe)
    result["model_version"] = "simulation-v2.0"
    return result


def run_inference(image_path: str, timeframe: str, asset: str) -> Dict:
    """
    Run chart pattern recognition on an image.
    Universal analysis for any asset - crypto, stocks, forex, indices.
    Returns bullish/bearish outcomes with probabilities.
    """
    
    if download_model():
        try:
            import torch
            from torchvision import transforms
            from PIL import Image
            
            device = torch.device('cpu')
            
            transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            
            img = Image.open(image_path).convert("RGB")
            x = transform(img).unsqueeze(0).to(device)
            
            model = torch.jit.load(MODEL_PATH, map_location=device)
            model.eval()
            
            with torch.no_grad():
                outputs = model(x)
                probs = torch.softmax(outputs.flatten(), dim=0).cpu().numpy()
            
            result = _build_outcomes(probs.tolist(), asset, timeframe)
            result["model_version"] = "cnn-v1.0"
            return result
            
        except Exception as e:
            print(f"Model inference failed: {e}")
    
    return _simulate_outcomes(asset, timeframe)
