"""
Pluggable model runner for chart analysis.
Returns 3 bullish + 3 bearish outcomes with probabilities.
Replace _simulate_outcomes with real ML model when ready.
"""
import os
import random

MODEL_PATH = os.getenv("CHART_MODEL_PATH", "/app/ml_models/chart_classifier.pt")

def _simulate_outcomes(asset: str, timeframe: str) -> dict:
    """Generate realistic-looking simulated outcomes for demo/fallback"""
    
    # Seed based on asset for consistent results per asset
    random.seed(hash(asset + timeframe) % 10000)
    
    # Generate probabilities that sum reasonably
    bull_probs = sorted([random.uniform(0.08, 0.45) for _ in range(3)], reverse=True)
    bear_probs = sorted([random.uniform(0.03, 0.20) for _ in range(3)], reverse=True)
    
    bulls = [
        {"name": "Breakout Continuation", "probability": round(bull_probs[0], 2), 
         "explanation": f"Price structure suggests upward momentum on {timeframe} timeframe."},
        {"name": "Support Bounce", "probability": round(bull_probs[1], 2),
         "explanation": "Key support level holding with increasing buy volume."},
        {"name": "Trend Reversal Up", "probability": round(bull_probs[2], 2),
         "explanation": "Oversold conditions with bullish divergence forming."}
    ]
    
    bears = [
        {"name": "Resistance Rejection", "probability": round(bear_probs[0], 2),
         "explanation": "Price approaching major resistance with weakening momentum."},
        {"name": "Breakdown Risk", "probability": round(bear_probs[1], 2),
         "explanation": "Support level under pressure, distribution pattern visible."},
        {"name": "Trend Reversal Down", "probability": round(bear_probs[2], 2),
         "explanation": "Overbought conditions with bearish divergence."}
    ]
    
    # Determine recommendation based on highest probability
    max_bull = max(bull_probs)
    max_bear = max(bear_probs)
    
    if max_bull > max_bear + 0.1:
        side = "buy"
        prob = max_bull
        rationale = "Bullish signals dominate with favorable risk/reward setup."
    elif max_bear > max_bull + 0.1:
        side = "sell"
        prob = max_bear
        rationale = "Bearish pressure detected, consider defensive positioning."
    else:
        side = "wait"
        prob = max(max_bull, max_bear)
        rationale = "Mixed signals - wait for clearer price action confirmation."
    
    return {
        "bullish": bulls,
        "bearish": bears,
        "recommended_trade": {"side": side, "probability": round(prob, 2), "rationale": rationale},
        "model_version": "simulation-v1.0"
    }


def run_inference(image_path: str, timeframe: str, asset: str) -> dict:
    """
    Main inference function. Replace with real ML model when ready.
    For now returns simulated outcomes.
    """
    # Check if real model exists
    if os.path.exists(MODEL_PATH):
        try:
            import torch
            from torchvision import transforms
            from PIL import Image
            
            t = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            
            img = Image.open(image_path).convert("RGB")
            x = t(img).unsqueeze(0)
            
            model = torch.jit.load(MODEL_PATH)
            model.eval()
            
            with torch.no_grad():
                out = model(x)
                probs = torch.softmax(out.flatten(), dim=0).cpu().numpy()
                
                bulls = [{"name": f"Bull Pattern {i+1}", "probability": float(probs[i]), 
                         "explanation": "Model-detected bullish signal."} for i in range(3)]
                bears = [{"name": f"Bear Pattern {i+1}", "probability": float(probs[3+i]),
                         "explanation": "Model-detected bearish signal."} for i in range(3)]
                
                rec = max(bulls + bears, key=lambda d: d["probability"])
                side = "buy" if rec in bulls else "sell"
                
                return {
                    "bullish": bulls,
                    "bearish": bears,
                    "recommended_trade": {"side": side, "probability": rec["probability"], "rationale": rec["explanation"]},
                    "model_version": "pytorch-v1.0"
                }
        except Exception as e:
            print(f"Model inference failed: {e}")
            return _simulate_outcomes(asset, timeframe)
    
    # No model file - use simulation
    return _simulate_outcomes(asset, timeframe)
