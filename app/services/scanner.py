from datetime import datetime
from sqlalchemy.orm import Session
from app.services.oracle import oracle
from app.models.signal import Signal
from app.core.logging import logger

class SignalScanner:
    """Automatically scan markets and save signals"""
    
    MIN_SCORE_TO_SAVE = 55  # Save signals with score >= 55 or <= 45
    
    async def scan_and_save(self, db: Session) -> dict:
        """Scan all assets and save actionable signals"""
        
        logger.info("Starting automated market scan...")
        
        saved_signals = []
        skipped = []
        errors = []
        
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
                    
                    logger.info(f"Saved: {symbol} - {signal_data['signal_type']} - Score: {score}")
                else:
                    skipped.append({"symbol": symbol, "score": score, "reason": "Score not actionable"})
                    
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")
                errors.append({"symbol": symbol, "error": str(e)})
        
        db.commit()
        
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_scanned": len(oracle.SUPPORTED_ASSETS),
            "saved": len(saved_signals),
            "skipped": len(skipped),
            "errors": len(errors),
            "saved_signals": saved_signals,
        }
        
        logger.info(f"Scan complete: {result['saved']} signals saved")
        
        return result

scanner = SignalScanner()
