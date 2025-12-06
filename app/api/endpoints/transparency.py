from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional
from datetime import datetime, timedelta
from app.db.session import get_db
from app.models.signal import Signal

router = APIRouter()

@router.get("/signals")
async def get_historical_signals(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    symbol: Optional[str] = None,
    signal_type: Optional[str] = None,
    status: Optional[str] = None,
    min_score: int = Query(0, ge=0, le=100),
    days: int = Query(30, ge=1, le=365)
):
    """
    Public endpoint: View all historical signals for transparency.
    All signals are timestamped and auditable.
    """
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    query = db.query(Signal).filter(Signal.created_at >= cutoff)
    
    if symbol:
        query = query.filter(Signal.symbol == symbol.upper())
    if signal_type:
        query = query.filter(Signal.signal_type == signal_type)
    if status:
        query = query.filter(Signal.status == status)
    if min_score > 0:
        query = query.filter(Signal.oracle_score >= min_score)
    
    total = query.count()
    offset = (page - 1) * per_page
    
    signals = query.order_by(desc(Signal.created_at)).offset(offset).limit(per_page).all()
    
    return {
        "disclaimer": "Past performance does not guarantee future results. See /legal/disclaimer for full details.",
        "period_days": days,
        "total": total,
        "page": page,
        "per_page": per_page,
        "signals": [
            {
                "id": s.id,
                "timestamp": s.created_at.isoformat() if s.created_at else None,
                "symbol": s.symbol,
                "pair": s.pair,
                "signal_type": s.signal_type,
                "oracle_score": s.oracle_score,
                "entry_price": s.entry_price,
                "target_price": s.target_price,
                "stop_loss": s.stop_loss,
                "risk_reward_ratio": s.risk_reward_ratio,
                "timeframe": s.timeframe,
                "expires_at": s.expires_at.isoformat() if s.expires_at else None,
                "status": s.status,
                "outcome_price": s.outcome_price,
                "outcome_pnl_percent": s.outcome_pnl_percent,
                "outcome_at": s.outcome_at.isoformat() if s.outcome_at else None,
                "model_version": s.model_version,
                "data_sources": s.data_sources,
                "reasoning_summary": s.reasoning_summary,
            }
            for s in signals
        ]
    }


@router.get("/performance")
async def get_performance_metrics(
    db: Session = Depends(get_db),
    days: int = Query(30, ge=7, le=365)
):
    """
    Public endpoint: View aggregated performance metrics.
    Full transparency on signal outcomes.
    """
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Get all signals in period
    all_signals = db.query(Signal).filter(Signal.created_at >= cutoff).all()
    
    # Get completed signals (have an outcome)
    completed = [s for s in all_signals if s.status in ["hit_target", "hit_stop", "expired"]]
    
    # Active signals
    active = [s for s in all_signals if s.status == "active"]
    
    if not completed:
        return {
            "disclaimer": "Past performance does not guarantee future results.",
            "period_days": days,
            "total_signals": len(all_signals),
            "completed_signals": 0,
            "active_signals": len(active),
            "metrics": {
                "win_rate": None,
                "avg_return_percent": None,
                "total_return_percent": None,
                "best_signal": None,
                "worst_signal": None,
            },
            "by_asset": {},
            "by_signal_type": {},
            "score_calibration": {},
            "message": "Insufficient completed signals for performance calculation"
        }
    
    # Calculate metrics
    wins = [s for s in completed if s.status == "hit_target"]
    losses = [s for s in completed if s.status in ["hit_stop", "expired"]]
    
    returns = [s.outcome_pnl_percent for s in completed if s.outcome_pnl_percent is not None]
    avg_return = sum(returns) / len(returns) if returns else 0
    total_return = sum(returns) if returns else 0
    
    best = max(completed, key=lambda x: x.outcome_pnl_percent or -999) if completed else None
    worst = min(completed, key=lambda x: x.outcome_pnl_percent or 999) if completed else None
    
    # By asset breakdown
    assets = set(s.symbol for s in completed)
    by_asset = {}
    for asset in assets:
        asset_signals = [s for s in completed if s.symbol == asset]
        asset_wins = [s for s in asset_signals if s.status == "hit_target"]
        asset_returns = [s.outcome_pnl_percent for s in asset_signals if s.outcome_pnl_percent is not None]
        by_asset[asset] = {
            "total": len(asset_signals),
            "wins": len(asset_wins),
            "win_rate": round(len(asset_wins) / len(asset_signals) * 100, 1) if asset_signals else 0,
            "avg_return": round(sum(asset_returns) / len(asset_returns), 2) if asset_returns else 0,
        }
    
    # By signal type
    by_type = {}
    for stype in ["buy", "sell", "hold"]:
        type_signals = [s for s in completed if s.signal_type == stype]
        type_wins = [s for s in type_signals if s.status == "hit_target"]
        type_returns = [s.outcome_pnl_percent for s in type_signals if s.outcome_pnl_percent is not None]
        if type_signals:
            by_type[stype] = {
                "total": len(type_signals),
                "wins": len(type_wins),
                "win_rate": round(len(type_wins) / len(type_signals) * 100, 1),
                "avg_return": round(sum(type_returns) / len(type_returns), 2) if type_returns else 0,
            }
    
    # Score calibration (do higher scores perform better?)
    score_brackets = {
        "50-59": [s for s in completed if 50 <= s.oracle_score < 60],
        "60-69": [s for s in completed if 60 <= s.oracle_score < 70],
        "70-79": [s for s in completed if 70 <= s.oracle_score < 80],
        "80-89": [s for s in completed if 80 <= s.oracle_score < 90],
        "90-100": [s for s in completed if 90 <= s.oracle_score <= 100],
    }
    
    score_calibration = {}
    for bracket, signals in score_brackets.items():
        if signals:
            bracket_wins = [s for s in signals if s.status == "hit_target"]
            bracket_returns = [s.outcome_pnl_percent for s in signals if s.outcome_pnl_percent is not None]
            score_calibration[bracket] = {
                "total": len(signals),
                "win_rate": round(len(bracket_wins) / len(signals) * 100, 1),
                "avg_return": round(sum(bracket_returns) / len(bracket_returns), 2) if bracket_returns else 0,
            }
    
    return {
        "disclaimer": "Past performance does not guarantee future results. Trading involves risk of loss.",
        "period_days": days,
        "generated_at": datetime.utcnow().isoformat(),
        "total_signals": len(all_signals),
        "completed_signals": len(completed),
        "active_signals": len(active),
        "metrics": {
            "win_rate": round(len(wins) / len(completed) * 100, 1),
            "loss_rate": round(len(losses) / len(completed) * 100, 1),
            "avg_return_percent": round(avg_return, 2),
            "total_return_percent": round(total_return, 2),
            "best_signal": {
                "id": best.id,
                "symbol": best.symbol,
                "return_percent": best.outcome_pnl_percent,
                "date": best.created_at.isoformat() if best.created_at else None,
            } if best and best.outcome_pnl_percent else None,
            "worst_signal": {
                "id": worst.id,
                "symbol": worst.symbol,
                "return_percent": worst.outcome_pnl_percent,
                "date": worst.created_at.isoformat() if worst.created_at else None,
            } if worst and worst.outcome_pnl_percent else None,
        },
        "by_asset": by_asset,
        "by_signal_type": by_type,
        "score_calibration": score_calibration,
    }


@router.get("/signal/{signal_id}")
async def get_signal_audit(
    signal_id: int,
    db: Session = Depends(get_db)
):
    """
    Public endpoint: Get full audit trail for a specific signal.
    Complete transparency on inputs, reasoning, and outcome.
    """
    
    signal = db.query(Signal).filter(Signal.id == signal_id).first()
    
    if not signal:
        return {"error": "Signal not found"}
    
    return {
        "disclaimer": "This is a historical record for transparency purposes.",
        "signal_id": signal.id,
        "audit_trail": {
            "created_at": signal.created_at.isoformat() if signal.created_at else None,
            "model_version": signal.model_version,
            "data_sources": signal.data_sources,
        },
        "signal_details": {
            "asset_type": signal.asset_type,
            "symbol": signal.symbol,
            "pair": signal.pair,
            "signal_type": signal.signal_type,
            "oracle_score": signal.oracle_score,
            "confidence": signal.confidence,
        },
        "price_targets": {
            "entry_price": signal.entry_price,
            "target_price": signal.target_price,
            "stop_loss": signal.stop_loss,
            "risk_reward_ratio": signal.risk_reward_ratio,
        },
        "analysis": {
            "reasoning_summary": signal.reasoning_summary,
            "reasoning_factors": signal.reasoning_factors,
            "timeframe": signal.timeframe,
            "expires_at": signal.expires_at.isoformat() if signal.expires_at else None,
        },
        "input_snapshot": signal.input_snapshot,
        "outcome": {
            "status": signal.status,
            "outcome_price": signal.outcome_price,
            "outcome_pnl_percent": signal.outcome_pnl_percent,
            "outcome_at": signal.outcome_at.isoformat() if signal.outcome_at else None,
        }
    }


@router.get("/summary")
async def get_transparency_summary(db: Session = Depends(get_db)):
    """
    Public endpoint: Quick summary of platform transparency metrics.
    """
    
    total_signals = db.query(Signal).count()
    
    # Get date range
    first_signal = db.query(Signal).order_by(Signal.created_at.asc()).first()
    last_signal = db.query(Signal).order_by(Signal.created_at.desc()).first()
    
    # Outcomes
    completed = db.query(Signal).filter(Signal.status.in_(["hit_target", "hit_stop", "expired"])).count()
    active = db.query(Signal).filter(Signal.status == "active").count()
    
    return {
        "platform": "ELUXRAJ",
        "transparency_commitment": "All signals are logged, timestamped, and publicly auditable.",
        "total_signals_generated": total_signals,
        "signals_with_outcomes": completed,
        "active_signals": active,
        "data_range": {
            "first_signal": first_signal.created_at.isoformat() if first_signal and first_signal.created_at else None,
            "last_signal": last_signal.created_at.isoformat() if last_signal and last_signal.created_at else None,
        },
        "links": {
            "historical_signals": "/api/v1/transparency/signals",
            "performance_metrics": "/api/v1/transparency/performance",
            "methodology": "/legal/methodology",
            "terms": "/legal/terms",
            "privacy": "/legal/privacy",
            "disclaimer": "/legal/disclaimer",
        },
        "disclaimer": "Past performance does not guarantee future results. See /legal/disclaimer for full details."
    }
