"""Chart Analysis V2 - AI Vision Trade Intelligence"""
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import os
import shutil
import json
from uuid import uuid4

from app.db.session import get_db
from app.core.deps import get_current_user
from app.core.logging import logger
from app.services.trade_intelligence import trade_intelligence

router = APIRouter()

UPLOADS_DIR = os.getenv("UPLOADS_DIR", "/tmp/eluxraj_uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

ALLOWED_TIMEFRAMES = {"5m", "15m", "30m", "1h", "2h", "4h", "8h", "12h", "24h", "1d", "3d", "1w", "1M"}

@router.post("/analyze")
async def analyze_chart(
    asset: str = Form(..., description="Ticker symbol, e.g. BTC, AAPL, EUR/USD"),
    timeframe: str = Form(..., description="Chart timeframe"),
    file: UploadFile = File(...),
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a chart image and receive AI-powered trade intelligence:
    - Pattern Detection
    - Market Structure Analysis
    - 3 Bullish Scenarios with probabilities
    - 3 Bearish Scenarios with probabilities
    - Trade Setup (if applicable)
    - Risk/Reward Analysis
    - Invalidation Conditions
    """
    # Check tier
    if user.subscription_tier not in ["pro", "elite", "admin"]:
        raise HTTPException(status_code=403, detail="Pro or Elite subscription required for Chart Analysis")
    
    # Validate timeframe
    timeframe = timeframe.strip()
    if timeframe not in ALLOWED_TIMEFRAMES:
        raise HTTPException(status_code=400, detail=f"Invalid timeframe. Must be one of: {sorted(ALLOWED_TIMEFRAMES)}")
    
    # Validate file
    content_type = file.content_type or ""
    filename = (file.filename or "").lower()
    if not (content_type.startswith("image/") or filename.endswith((".png", ".jpg", ".jpeg"))):
        raise HTTPException(status_code=400, detail="File must be an image (PNG, JPG, JPEG)")
    
    # Save file
    upload_id = str(uuid4())
    ext = os.path.splitext(filename)[1] or ".jpg"
    saved_path = os.path.join(UPLOADS_DIR, f"{upload_id}{ext}")
    
    try:
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"Chart uploaded: {saved_path} for {asset} ({timeframe})")
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to save upload")
    
    # Run AI analysis
    analysis = await trade_intelligence.analyze_chart_image(
        image_path=saved_path,
        asset=asset.upper(),
        timeframe=timeframe
    )
    
    # Build response
    return {
        "analysis_id": upload_id,
        "asset": asset.upper(),
        "timeframe": timeframe,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pattern_detected": analysis.get("pattern_detected", "none"),
        "market_structure": analysis.get("market_structure", "unclear"),
        "key_levels": analysis.get("key_levels", {"support": [], "resistance": []}),
        "bullish_scenarios": analysis.get("bullish_scenarios", []),
        "bearish_scenarios": analysis.get("bearish_scenarios", []),
        "trade_recommendation": analysis.get("trade_recommendation", "no_trade"),
        "trade_setup": analysis.get("trade_setup"),
        "confidence_score": analysis.get("confidence_score", 0),
        "invalidation_conditions": analysis.get("invalidation_conditions", []),
        "reasoning": analysis.get("reasoning", ""),
        "disclaimer": "ELUXRAJ provides AI-powered decision intelligence for informational purposes only. This is NOT financial advice. All trading involves risk."
    }

@router.get("/history")
async def get_analysis_history(
    user = Depends(get_current_user),
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get user's chart analysis history"""
    # For now return empty - can implement with ChartAnalysisV2 model
    return {"count": 0, "analyses": []}
