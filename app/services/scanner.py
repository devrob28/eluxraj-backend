from datetime import datetime
from sqlalchemy.orm import Session
from app.services.oracle import oracle
from app.services.email import email_service
from app.models.signal import Signal
from app.models.user import User
from app.core.logging import logger

class SignalScanner:
    """Automatically scan markets and save signals"""
    
    MIN_SCORE_TO_SAVE = 55
    MIN_SCORE_TO_ALERT = 70  # Only alert for high-confidence signals
    
    async def scan_and_save(self, db: Session) -> dict:
        """Scan all assets and save actionable signals"""
        
        logger.info("🔍 Starting automated market scan...")
        
        saved_signals = []
        skipped = []
        errors = []
        alerts_sent = 0
        
        for symbol in oracle.SUPPORTED_ASSETS:
            try:
                signal_data = await oracle.generate_signal(symbol)
                
                if not signal_data:
                    errors.append({"symbol": symbol, "error": "No data"})
                    continue
                
                score = signal_data["oracle_score"]
                
                # Only save actionable signals
                if score >= self.MIN_SCORE_TO_SAVE or score <= (100 - self.MIN_SCORE_TO_SAVE):
                    signal = Signal(
                        asset_type=signal_data["asset_type"],
                        symbol=signal_data["symbol"],
                        pair=signal_data["pair"],
                        signal_type=signal_data["signal_type"],
                        oracle_score=signal_data["oracle_score"],
                        confidence=signal_data["confidence"],
                        entry_price=signal_data["entry_price"],
                        target_price=signal_data["target_price"],
                        stop_loss=signal_data["stop_loss"],
                        risk_reward_ratio=signal_data["risk_reward_ratio"],
                        reasoning_summary=signal_data["reasoning_summary"],
                        reasoning_factors=signal_data["reasoning_factors"],
                        model_version=signal_data["model_version"],
                        input_snapshot=signal_data["input_snapshot"],
                        data_sources=signal_data["data_sources"],
                        timeframe=signal_data["timeframe"],
                        expires_at=datetime.fromisoformat(signal_data["expires_at"]),
                        status="active",
                    )
                    
                    db.add(signal)
                    saved_signals.append({
                        "symbol": symbol,
                        "signal_type": signal_data["signal_type"],
                        "score": score,
                    })
                    
                    logger.info(f"💾 Saved: {symbol} - {signal_data['signal_type']} - Score: {score}")
                    
                    # Send alerts for high-confidence signals
                    if score >= self.MIN_SCORE_TO_ALERT and email_service.is_enabled():
                        alert_count = await self._send_alerts_to_users(db, signal_data)
                        alerts_sent += alert_count
                else:
                    skipped.append({"symbol": symbol, "score": score, "reason": "Score not actionable"})
                    
            except Exception as e:
                logger.error(f"❌ Error scanning {symbol}: {e}")
                errors.append({"symbol": symbol, "error": str(e)})
        
        db.commit()
        
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_scanned": len(oracle.SUPPORTED_ASSETS),
            "saved": len(saved_signals),
            "skipped": len(skipped),
            "errors": len(errors),
            "alerts_sent": alerts_sent,
            "saved_signals": saved_signals,
        }
        
        logger.info(f"✅ Scan complete: {result['saved']} signals saved, {alerts_sent} alerts sent")
        
        return result
    
    async def _send_alerts_to_users(self, db: Session, signal_data: dict) -> int:
        """Send email alerts to subscribed users"""
        
        # Get users who have alerts enabled and are Pro/Elite
        users = db.query(User).filter(
            User.email_alerts == True,
            User.is_active == True,
            User.subscription_tier.in_(["pro", "elite"])
        ).all()
        
        sent_count = 0
        
        for user in users:
            try:
                success = await email_service.send_signal_alert(
                    user.email,
                    user.full_name,
                    signal_data
                )
                if success:
                    sent_count += 1
                    logger.info(f"📧 Alert sent to {user.email}")
            except Exception as e:
                logger.error(f"❌ Failed to send alert to {user.email}: {e}")
        
        return sent_count


scanner = SignalScanner()
