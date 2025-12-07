from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import os
import shutil
import json
from uuid import uuid4

from app.db.session import get_db
from app.models.chart import ChartUpload, ChartAnalysisResult
from app.ml.model_runner import run_inference
from app.core.logging import logger

router = APIRouter()

# Config
UPLOADS_DIR = os.getenv("UPLOADS_DIR", "/tmp/eluxraj_uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

ALLOWED_TIMEFRAMES = {"5m", "15m", "30m", "1h", "2h", "4h", "8h", "12h", "24h", "3d", "1M"}


def save_upload(file: UploadFile, upload_id: str) -> str:
    """Save uploaded file and return path"""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in [".png", ".jpg", ".jpeg"]:
        ext = ".jpg"
    
    filename = f"{upload_id}{ext}"
    path = os.path.join(UPLOADS_DIR, filename)
    
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return path


@router.post("/analyze")
async def analyze_chart(
    asset: str = Form(..., description="Ticker symbol, e.g. BTC-USD, AAPL"),
    timeframe: str = Form(..., description="Chart timeframe: 5m,15m,30m,1h,2h,4h,8h,12h,24h,3d,1M"),
    file: UploadFile = File(...),
    user_id: int = Form(None),
    db: Session = Depends(get_db)
):
    """
    Analyze a chart image and return bullish/bearish outcomes with probabilities.
    """
    # Validate timeframe
    timeframe = timeframe.strip()
    if timeframe not in ALLOWED_TIMEFRAMES:
        raise HTTPException(status_code=400, detail=f"Invalid timeframe. Must be one of: {sorted(ALLOWED_TIMEFRAMES)}")
    
    # Validate file type
    content_type = file.content_type or ""
    filename = (file.filename or "").lower()
    if not (content_type.startswith("image/") or filename.endswith((".png", ".jpg", ".jpeg"))):
        raise HTTPException(status_code=400, detail="File must be an image (PNG, JPG, JPEG)")
    
    # Save file
    upload_id = str(uuid4())
    try:
        saved_path = save_upload(file, upload_id)
        logger.info(f"Chart uploaded: {saved_path} for {asset} ({timeframe})")
    except Exception as e:
        logger.error(f"Failed to save upload: {e}")
        raise HTTPException(status_code=500, detail="Failed to save upload")
    
    # Run ML inference
    try:
        inference = run_inference(saved_path, timeframe, asset)
    except Exception as e:
        logger.error(f"Inference failed: {e}")
        # Return fallback response
        inference = {
            "bullish": [
                {"name": "Analysis Pending", "probability": 0.33, "explanation": "Unable to process chart."}
            ],
            "bearish": [
                {"name": "Analysis Pending", "probability": 0.33, "explanation": "Unable to process chart."}
            ],
            "recommended_trade": {"side": "wait", "probability": 0.33, "rationale": "Analysis unavailable."},
            "model_version": "fallback"
        }
    
    # Save to database
    try:
        # Save upload record
        chart_upload = ChartUpload(
            user_id=user_id,
            asset=asset.upper(),
            timeframe=timeframe,
            file_path=saved_path
        )
        db.add(chart_upload)
        db.commit()
        db.refresh(chart_upload)
        
        # Save analysis result
        analysis_result = ChartAnalysisResult(
            upload_id=chart_upload.id,
            asset=asset.upper(),
            timeframe=timeframe,
            result_json=json.dumps(inference),
            model_version=inference.get("model_version", "unknown")
        )
        db.add(analysis_result)
        db.commit()
        db.refresh(analysis_result)
        
        analysis_id = analysis_result.id
    except Exception as e:
        logger.error(f"DB save failed: {e}")
        db.rollback()
        analysis_id = upload_id  # Use upload_id as fallback
    
    # Build response
    now = datetime.now(timezone.utc).isoformat()
    
    return {
        "analysis_id": str(analysis_id),
        "asset": asset.upper(),
        "timeframe": timeframe,
        "generated_at": now,
        "bullish": inference["bullish"],
        "bearish": inference["bearish"],
        "recommended_trade": inference["recommended_trade"],
        "model_version": inference.get("model_version", "unknown"),
        "disclaimer": "ELUXRAJ provides AI-powered analysis for informational purposes only. This is NOT financial advice. Always do your own research."
    }


@router.get("/history")
async def get_analysis_history(
    user_id: int = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get recent chart analysis history"""
    query = db.query(ChartAnalysisResult).order_by(ChartAnalysisResult.created_at.desc())
    
    if user_id:
        query = query.join(ChartUpload).filter(ChartUpload.user_id == user_id)
    
    results = query.limit(limit).all()
    
    return {
        "count": len(results),
        "analyses": [
            {
                "id": r.id,
                "asset": r.asset,
                "timeframe": r.timeframe,
                "result": json.loads(r.result_json),
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in results
        ]
    }
