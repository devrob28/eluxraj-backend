"""
ELUXRAJ Alert System
Level 1: Automated alerts for ORACLE signals and whale movements
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel
from app.db.session import get_db, Base
from app.core.deps import get_current_user
from app.core.logging import logger
import httpx

router = APIRouter()


# ============== MODELS ==============

class AlertRule(Base):
    """User-defined alert rules"""
    __tablename__ = "alert_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    asset = Column(String, nullable=False)  # BTC, ETH, AAPL, etc.
    asset_type = Column(String, default="crypto")  # crypto, stock
    
    # Trigger conditions
    trigger_type = Column(String, nullable=False)  # oracle_score, price, whale_movement, volume
    condition = Column(String, nullable=False)  # above, below, crosses_above, crosses_below
    threshold = Column(Float, nullable=False)
    
    # Notification settings
    notify_email = Column(Boolean, default=True)
    notify_push = Column(Boolean, default=True)
    notify_sms = Column(Boolean, default=False)
    webhook_url = Column(String, nullable=True)
    
    # State
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, default=0)
    cooldown_minutes = Column(Integer, default=60)  # Don't re-trigger for X minutes
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class AlertHistory(Base):
    """Log of triggered alerts"""
    __tablename__ = "alert_history"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("alert_rules.id"), nullable=False)
    user_id = Column(Integer, nullable=False)
    
    asset = Column(String, nullable=False)
    trigger_type = Column(String, nullable=False)
    trigger_value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    
    message = Column(String, nullable=False)
    notification_sent = Column(Boolean, default=False)
    notification_channels = Column(JSON, default=list)
    
    triggered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class PortfolioScan(Base):
    """Scheduled portfolio scan results"""
    __tablename__ = "portfolio_scans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    assets_scanned = Column(Integer, default=0)
    signals = Column(JSON, default=list)  # List of {asset, score, signal, change}
    summary = Column(String, nullable=True)
    
    scanned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ============== SCHEMAS ==============

class AlertRuleCreate(BaseModel):
    name: str
    asset: str
    asset_type: str = "crypto"
    trigger_type: str  # oracle_score, price, whale_movement
    condition: str  # above, below, crosses_above, crosses_below
    threshold: float
    notify_email: bool = True
    notify_push: bool = True
    notify_sms: bool = False
    webhook_url: Optional[str] = None
    cooldown_minutes: int = 60


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    threshold: Optional[float] = None
    is_active: Optional[bool] = None
    notify_email: Optional[bool] = None
    notify_push: Optional[bool] = None
    cooldown_minutes: Optional[int] = None


# ============== NOTIFICATION SERVICE ==============

async def send_notification(user_id: int, alert: AlertHistory, channels: List[str], db: Session):
    """Send notifications through specified channels"""
    from app.models.user import User
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return
    
    sent_channels = []
    
    # Email notification
    if "email" in channels and user.email:
        try:
            # TODO: Integrate with SendGrid/SES
            logger.info(f"Email alert to {user.email}: {alert.message}")
            sent_channels.append("email")
        except Exception as e:
            logger.error(f"Email notification failed: {e}")
    
    # Push notification
    if "push" in channels:
        try:
            # TODO: Integrate with Firebase/OneSignal
            logger.info(f"Push alert to user {user_id}: {alert.message}")
            sent_channels.append("push")
        except Exception as e:
            logger.error(f"Push notification failed: {e}")
    
    # Webhook
    if "webhook" in channels:
        rule = db.query(AlertRule).filter(AlertRule.id == alert.rule_id).first()
        if rule and rule.webhook_url:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(rule.webhook_url, json={
                        "alert_id": alert.id,
                        "asset": alert.asset,
                        "trigger_type": alert.trigger_type,
                        "value": alert.trigger_value,
                        "threshold": alert.threshold,
                        "message": alert.message,
                        "triggered_at": alert.triggered_at.isoformat()
                    }, timeout=10.0)
                sent_channels.append("webhook")
            except Exception as e:
                logger.error(f"Webhook notification failed: {e}")
    
    # Update alert history
    alert.notification_sent = len(sent_channels) > 0
    alert.notification_channels = sent_channels
    db.commit()


async def check_and_trigger_alerts(asset: str, trigger_type: str, current_value: float, db: Session):
    """Check all active rules and trigger alerts if conditions are met"""
    from datetime import timedelta
    
    rules = db.query(AlertRule).filter(
        AlertRule.asset == asset,
        AlertRule.trigger_type == trigger_type,
        AlertRule.is_active == True
    ).all()
    
    now = datetime.now(timezone.utc)
    
    for rule in rules:
        # Check cooldown
        if rule.last_triggered:
            cooldown_end = rule.last_triggered + timedelta(minutes=rule.cooldown_minutes)
            if now < cooldown_end:
                continue
        
        # Check condition
        triggered = False
        if rule.condition == "above" and current_value > rule.threshold:
            triggered = True
        elif rule.condition == "below" and current_value < rule.threshold:
            triggered = True
        elif rule.condition == "crosses_above" and current_value > rule.threshold:
            triggered = True  # TODO: Track previous value for true crossover
        elif rule.condition == "crosses_below" and current_value < rule.threshold:
            triggered = True
        
        if triggered:
            # Create alert message
            message = f"🚨 {asset} Alert: {trigger_type} is {current_value:.2f} ({rule.condition} {rule.threshold})"
            
            # Log alert
            alert = AlertHistory(
                rule_id=rule.id,
                user_id=rule.user_id,
                asset=asset,
                trigger_type=trigger_type,
                trigger_value=current_value,
                threshold=rule.threshold,
                message=message
            )
            db.add(alert)
            
            # Update rule
            rule.last_triggered = now
            rule.trigger_count += 1
            db.commit()
            db.refresh(alert)
            
            # Determine channels
            channels = []
            if rule.notify_email:
                channels.append("email")
            if rule.notify_push:
                channels.append("push")
            if rule.webhook_url:
                channels.append("webhook")
            
            # Send notifications
            await send_notification(rule.user_id, alert, channels, db)
            
            logger.info(f"Alert triggered: {message}")


# ============== API ENDPOINTS ==============

@router.post("/rules")
async def create_alert_rule(
    rule: AlertRuleCreate,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new alert rule"""
    # Validate trigger type
    valid_triggers = ["oracle_score", "price", "whale_movement", "volume", "rsi", "macd"]
    if rule.trigger_type not in valid_triggers:
        raise HTTPException(status_code=400, detail=f"Invalid trigger type. Must be one of: {valid_triggers}")
    
    # Validate condition
    valid_conditions = ["above", "below", "crosses_above", "crosses_below"]
    if rule.condition not in valid_conditions:
        raise HTTPException(status_code=400, detail=f"Invalid condition. Must be one of: {valid_conditions}")
    
    # Create rule
    db_rule = AlertRule(
        user_id=user.id,
        name=rule.name,
        asset=rule.asset.upper(),
        asset_type=rule.asset_type,
        trigger_type=rule.trigger_type,
        condition=rule.condition,
        threshold=rule.threshold,
        notify_email=rule.notify_email,
        notify_push=rule.notify_push,
        notify_sms=rule.notify_sms,
        webhook_url=rule.webhook_url,
        cooldown_minutes=rule.cooldown_minutes
    )
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    
    return {"ok": True, "rule_id": db_rule.id, "message": "Alert rule created"}


@router.get("/rules")
async def get_alert_rules(
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all alert rules for current user"""
    rules = db.query(AlertRule).filter(AlertRule.user_id == user.id).all()
    
    return {
        "ok": True,
        "count": len(rules),
        "rules": [
            {
                "id": r.id,
                "name": r.name,
                "asset": r.asset,
                "asset_type": r.asset_type,
                "trigger_type": r.trigger_type,
                "condition": r.condition,
                "threshold": r.threshold,
                "is_active": r.is_active,
                "last_triggered": r.last_triggered.isoformat() if r.last_triggered else None,
                "trigger_count": r.trigger_count,
                "notify_email": r.notify_email,
                "notify_push": r.notify_push,
                "cooldown_minutes": r.cooldown_minutes
            }
            for r in rules
        ]
    }


@router.patch("/rules/{rule_id}")
async def update_alert_rule(
    rule_id: int,
    updates: AlertRuleUpdate,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an alert rule"""
    rule = db.query(AlertRule).filter(
        AlertRule.id == rule_id,
        AlertRule.user_id == user.id
    ).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    
    # Apply updates
    if updates.name is not None:
        rule.name = updates.name
    if updates.threshold is not None:
        rule.threshold = updates.threshold
    if updates.is_active is not None:
        rule.is_active = updates.is_active
    if updates.notify_email is not None:
        rule.notify_email = updates.notify_email
    if updates.notify_push is not None:
        rule.notify_push = updates.notify_push
    if updates.cooldown_minutes is not None:
        rule.cooldown_minutes = updates.cooldown_minutes
    
    db.commit()
    
    return {"ok": True, "message": "Alert rule updated"}


@router.delete("/rules/{rule_id}")
async def delete_alert_rule(
    rule_id: int,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an alert rule"""
    rule = db.query(AlertRule).filter(
        AlertRule.id == rule_id,
        AlertRule.user_id == user.id
    ).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    
    db.delete(rule)
    db.commit()
    
    return {"ok": True, "message": "Alert rule deleted"}


@router.get("/history")
async def get_alert_history(
    limit: int = 50,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get alert history for current user"""
    alerts = db.query(AlertHistory).filter(
        AlertHistory.user_id == user.id
    ).order_by(AlertHistory.triggered_at.desc()).limit(limit).all()
    
    return {
        "ok": True,
        "count": len(alerts),
        "alerts": [
            {
                "id": a.id,
                "asset": a.asset,
                "trigger_type": a.trigger_type,
                "trigger_value": a.trigger_value,
                "threshold": a.threshold,
                "message": a.message,
                "notification_sent": a.notification_sent,
                "triggered_at": a.triggered_at.isoformat()
            }
            for a in alerts
        ]
    }


@router.post("/test/{rule_id}")
async def test_alert_rule(
    rule_id: int,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a test notification for an alert rule"""
    rule = db.query(AlertRule).filter(
        AlertRule.id == rule_id,
        AlertRule.user_id == user.id
    ).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    
    # Create test alert
    alert = AlertHistory(
        rule_id=rule.id,
        user_id=user.id,
        asset=rule.asset,
        trigger_type=rule.trigger_type,
        trigger_value=rule.threshold,
        threshold=rule.threshold,
        message=f"🧪 TEST: {rule.name} - This is a test notification"
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    # Send notifications
    channels = []
    if rule.notify_email:
        channels.append("email")
    if rule.notify_push:
        channels.append("push")
    if rule.webhook_url:
        channels.append("webhook")
    
    await send_notification(user.id, alert, channels, db)
    
    return {"ok": True, "message": "Test notification sent", "channels": channels}


# ============== PORTFOLIO SCAN ==============

@router.post("/scan")
async def scan_portfolio(
    assets: List[str] = None,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Scan assets and check all alert rules"""
    from app.services.oracle import oracle
    
    # Default assets to scan
    if not assets:
        assets = ["BTC", "ETH"]
    
    results = []
    
    for asset in assets:
        try:
            signal = await oracle.generate_signal(asset)
            if signal:
                score = signal.get("oracle_score", 50)
                signal_type = signal.get("signal_type", "hold")
                
                results.append({
                    "asset": asset,
                    "score": score,
                    "signal": signal_type,
                    "price": signal.get("entry_price"),
                    "change_24h": signal.get("price_change_24h")
                })
                
                # Check alerts for this asset
                await check_and_trigger_alerts(asset, "oracle_score", score, db)
                
        except Exception as e:
            logger.error(f"Scan error for {asset}: {e}")
    
    # Save scan result
    scan = PortfolioScan(
        user_id=user.id,
        assets_scanned=len(results),
        signals=results,
        summary=f"Scanned {len(results)} assets"
    )
    db.add(scan)
    db.commit()
    
    return {
        "ok": True,
        "scanned": len(results),
        "results": results,
        "scanned_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/scan/history")
async def get_scan_history(
    limit: int = 10,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get portfolio scan history"""
    scans = db.query(PortfolioScan).filter(
        PortfolioScan.user_id == user.id
    ).order_by(PortfolioScan.scanned_at.desc()).limit(limit).all()
    
    return {
        "ok": True,
        "count": len(scans),
        "scans": [
            {
                "id": s.id,
                "assets_scanned": s.assets_scanned,
                "signals": s.signals,
                "summary": s.summary,
                "scanned_at": s.scanned_at.isoformat()
            }
            for s in scans
        ]
    }
