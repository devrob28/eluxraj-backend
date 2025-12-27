"""Chart Analysis V2 - AI Vision Trade Intelligence"""
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import os
import shutil
from uuid import uuid4

from app.db.session import get_db
from app.core.deps import get_current_user
from app.core.logging import logger
from app.services.trade_intelligence import trade_intelligence
from app.services.rate_limiter import rate_limiter
from app.models.chart_analysis import ChartAnalysis

router = APIRouter()

UPLOADS_DIR = os.getenv("UPLOADS_DIR", "/tmp/eluxraj_uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

ALLOWED_TIMEFRAMES = {"5m", "15m", "30m", "1h", "2h", "4h", "8h", "12h", "24h", "1d", "3d", "1w", "1M"}


@router.post("/analyze")
async def analyze_chart(
    file: UploadFile = File(...),
    asset: str = Form(...),
    timeframe: str = Form("4h"),
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze a chart image using AI Vision.
    Returns:
    - Pattern Detection
    - Market Structure
    - Key Support/Resistance Levels
    - 3 Bullish Scenarios with probabilities
    - 3 Bearish Scenarios with probabilities
    - Trade Setup (if applicable)
    - Risk/Reward Analysis
    - Invalidation Conditions
    """
    # Check rate limit (also checks tier access)
    usage_info = rate_limiter.check_and_increment(
        db=db,
        user_id=user.id,
        tier=user.subscription_tier,
        feature="chart_analysis"
    )
    
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
    ext = filename.split(".")[-1] if "." in filename else "png"
    file_id = str(uuid4())
    file_path = os.path.join(UPLOADS_DIR, f"{file_id}.{ext}")
    
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        logger.info(f"Saved chart image: {file_path}")
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")
    
    # Analyze with AI
    try:
        logger.info(f"Analyzing chart for {asset} ({timeframe})")
        analysis = await trade_intelligence.analyze_chart_image(
            image_path=file_path,
            asset=asset.upper(),
            timeframe=timeframe
        )
        
        # Save to database
        try:
            chart_record = ChartAnalysis(
                user_id=user.id,
                asset=asset.upper(),
                timeframe=timeframe,
                pattern_detected=analysis.get("pattern_detected"),
                market_structure=analysis.get("market_structure"),
                key_levels=analysis.get("key_levels"),
                trade_recommendation=analysis.get("trade_recommendation"),
                trade_setup=analysis.get("trade_setup"),
                bullish_scenarios=analysis.get("bullish_scenarios"),
                bearish_scenarios=analysis.get("bearish_scenarios"),
                invalidation_conditions=analysis.get("invalidation_conditions"),
                confidence_score=analysis.get("confidence_score", 0),
                reasoning=analysis.get("reasoning"),
                status="active"
            )
            db.add(chart_record)
            db.commit()
            db.refresh(chart_record)
            analysis_id = chart_record.id
        except Exception as e:
            logger.error(f"Failed to save chart analysis: {e}")
            analysis_id = None
        
    except Exception as e:
        logger.error(f"Chart analysis failed: {e}")
        raise HTTPException(status_code=500, detail="AI analysis failed. Please try again.")
    finally:
        # Cleanup file
        try:
            os.remove(file_path)
        except:
            pass
    
    return {
        "analysis_id": analysis_id,
        "asset": asset.upper(),
        "timeframe": timeframe,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "usage": usage_info,
        **analysis,
        "disclaimer": "ELUXRAJ provides AI-powered decision intelligence for informational purposes only. This is NOT financial advice."
    }


@router.get("/history")
async def get_analysis_history(
    user = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(20, le=100)
):
    """Get user's chart analysis history"""
    analyses = db.query(ChartAnalysis).filter(
        ChartAnalysis.user_id == user.id
    ).order_by(ChartAnalysis.created_at.desc()).limit(limit).all()
    
    return {
        "count": len(analyses),
        "analyses": [_format_analysis(a) for a in analyses]
    }


@router.get("/{analysis_id}")
async def get_analysis(
    analysis_id: int,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific chart analysis"""
    analysis = db.query(ChartAnalysis).filter(
        ChartAnalysis.id == analysis_id,
        ChartAnalysis.user_id == user.id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return _format_analysis(analysis)


def _format_analysis(a: ChartAnalysis) -> dict:
    """Format analysis for API response"""
    return {
        "id": a.id,
        "asset": a.asset,
        "timeframe": a.timeframe,
        "pattern_detected": a.pattern_detected,
        "market_structure": a.market_structure,
        "key_levels": a.key_levels or {"support": [], "resistance": []},
        "trade_recommendation": a.trade_recommendation,
        "trade_setup": a.trade_setup,
        "bullish_scenarios": a.bullish_scenarios or [],
        "bearish_scenarios": a.bearish_scenarios or [],
        "invalidation_conditions": a.invalidation_conditions or [],
        "confidence_score": a.confidence_score,
        "reasoning": a.reasoning,
        "status": a.status,
        "created_at": a.created_at.isoformat() if a.created_at else None
    }
