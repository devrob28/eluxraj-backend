"""
Performance Tracking Service
Compare user trades against ELUXRAJ signals
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.performance import UserTrade, SignalHistory, PerformanceSnapshot
from app.core.logging import logger


class PerformanceService:
    """Track and analyze trading performance"""
    
    def add_user_trade(
        self,
        db: Session,
        user_id: int,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        asset_type: str = "crypto",
        source: str = "manual",
        signal_id: int = None
    ) -> UserTrade:
        """Record a user trade"""
        trade = UserTrade(
            user_id=user_id,
            symbol=symbol.upper(),
            asset_type=asset_type,
            side=side.lower(),
            quantity=quantity,
            price=price,
            total_value=quantity * price,
            source=source,
            signal_id=signal_id
        )
        db.add(trade)
        db.commit()
        db.refresh(trade)
        return trade
    
    def add_signal(
        self,
        db: Session,
        symbol: str,
        signal_type: str,
        entry_price: float,
        target_price: float = None,
        stop_loss: float = None,
        confidence: float = 70.0,
        reasoning: str = None,
        asset_type: str = "crypto"
    ) -> SignalHistory:
        """Record an ELUXRAJ signal"""
        signal = SignalHistory(
            symbol=symbol.upper(),
            asset_type=asset_type,
            signal_type=signal_type.lower(),
            entry_price=entry_price,
            target_price=target_price,
            stop_loss=stop_loss,
            confidence=confidence,
            reasoning=reasoning
        )
        db.add(signal)
        db.commit()
        db.refresh(signal)
        return signal
    
    def close_signal(
        self,
        db: Session,
        signal_id: int,
        exit_price: float
    ) -> Optional[SignalHistory]:
        """Close a signal and calculate outcome"""
        signal = db.query(SignalHistory).filter(SignalHistory.id == signal_id).first()
        if not signal:
            return None
        
        signal.exit_price = exit_price
        signal.closed_at = datetime.now(timezone.utc)
        
        # Calculate PnL
        if signal.signal_type == "buy":
            pnl = ((exit_price - signal.entry_price) / signal.entry_price) * 100
        else:  # sell/short
            pnl = ((signal.entry_price - exit_price) / signal.entry_price) * 100
        
        signal.pnl_percent = round(pnl, 2)
        signal.outcome = "win" if pnl > 0 else "loss"
        
        db.commit()
        db.refresh(signal)
        return signal
    
    def get_user_trades(
        self,
        db: Session,
        user_id: int,
        limit: int = 50,
        symbol: str = None
    ) -> List[Dict]:
        """Get user's trade history"""
        query = db.query(UserTrade).filter(UserTrade.user_id == user_id)
        
        if symbol:
            query = query.filter(UserTrade.symbol == symbol.upper())
        
        trades = query.order_by(UserTrade.executed_at.desc()).limit(limit).all()
        
        return [
            {
                "id": t.id,
                "symbol": t.symbol,
                "asset_type": t.asset_type,
                "side": t.side,
                "quantity": t.quantity,
                "price": t.price,
                "total_value": t.total_value,
                "source": t.source,
                "executed_at": t.executed_at.isoformat()
            }
            for t in trades
        ]
    
    def get_signal_history(
        self,
        db: Session,
        limit: int = 50,
        symbol: str = None,
        outcome: str = None
    ) -> List[Dict]:
        """Get ELUXRAJ signal history"""
        query = db.query(SignalHistory)
        
        if symbol:
            query = query.filter(SignalHistory.symbol == symbol.upper())
        if outcome:
            query = query.filter(SignalHistory.outcome == outcome)
        
        signals = query.order_by(SignalHistory.signal_time.desc()).limit(limit).all()
        
        return [
            {
                "id": s.id,
                "symbol": s.symbol,
                "signal_type": s.signal_type,
                "entry_price": s.entry_price,
                "target_price": s.target_price,
                "stop_loss": s.stop_loss,
                "exit_price": s.exit_price,
                "outcome": s.outcome,
                "pnl_percent": s.pnl_percent,
                "confidence": s.confidence,
                "reasoning": s.reasoning,
                "signal_time": s.signal_time.isoformat(),
                "closed_at": s.closed_at.isoformat() if s.closed_at else None
            }
            for s in signals
        ]
    
    def get_user_stats(self, db: Session, user_id: int, days: int = 30) -> Dict:
        """Get user's trading statistics"""
        since = datetime.now(timezone.utc) - timedelta(days=days)
        
        trades = db.query(UserTrade).filter(
            UserTrade.user_id == user_id,
            UserTrade.executed_at >= since
        ).all()
        
        if not trades:
            return {
                "total_trades": 0,
                "buy_trades": 0,
                "sell_trades": 0,
                "total_volume": 0,
                "unique_assets": 0,
                "most_traded": None
            }
        
        buy_trades = [t for t in trades if t.side == "buy"]
        sell_trades = [t for t in trades if t.side == "sell"]
        
        # Most traded asset
        symbol_counts = {}
        for t in trades:
            symbol_counts[t.symbol] = symbol_counts.get(t.symbol, 0) + 1
        most_traded = max(symbol_counts, key=symbol_counts.get) if symbol_counts else None
        
        return {
            "total_trades": len(trades),
            "buy_trades": len(buy_trades),
            "sell_trades": len(sell_trades),
            "total_volume": sum(t.total_value for t in trades),
            "unique_assets": len(set(t.symbol for t in trades)),
            "most_traded": most_traded,
            "period_days": days
        }
    
    def get_signal_stats(self, db: Session, days: int = 30) -> Dict:
        """Get ELUXRAJ signal statistics"""
        since = datetime.now(timezone.utc) - timedelta(days=days)
        
        signals = db.query(SignalHistory).filter(
            SignalHistory.signal_time >= since
        ).all()
        
        closed = [s for s in signals if s.outcome]
        wins = [s for s in closed if s.outcome == "win"]
        losses = [s for s in closed if s.outcome == "loss"]
        
        win_rate = (len(wins) / len(closed) * 100) if closed else 0
        avg_win = sum(s.pnl_percent for s in wins) / len(wins) if wins else 0
        avg_loss = sum(s.pnl_percent for s in losses) / len(losses) if losses else 0
        total_pnl = sum(s.pnl_percent for s in closed)
        
        return {
            "total_signals": len(signals),
            "closed_signals": len(closed),
            "open_signals": len(signals) - len(closed),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(win_rate, 1),
            "avg_win_percent": round(avg_win, 2),
            "avg_loss_percent": round(avg_loss, 2),
            "total_pnl_percent": round(total_pnl, 2),
            "period_days": days
        }
    
    def compare_performance(self, db: Session, user_id: int, days: int = 30) -> Dict:
        """Compare user performance vs ELUXRAJ signals"""
        user_stats = self.get_user_stats(db, user_id, days)
        signal_stats = self.get_signal_stats(db, days)
        
        since = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Check how many signals user followed
        user_trades = db.query(UserTrade).filter(
            UserTrade.user_id == user_id,
            UserTrade.executed_at >= since
        ).all()
        
        signals = db.query(SignalHistory).filter(
            SignalHistory.signal_time >= since
        ).all()
        
        # Match trades to signals (within 1 hour and same symbol/side)
        followed = 0
        for signal in signals:
            for trade in user_trades:
                if (trade.symbol == signal.symbol and 
                    trade.side == signal.signal_type and
                    abs((trade.executed_at - signal.signal_time).total_seconds()) < 3600):
                    followed += 1
                    break
        
        missed = len(signals) - followed
        follow_rate = (followed / len(signals) * 100) if signals else 0
        
        return {
            "user": user_stats,
            "signals": signal_stats,
            "comparison": {
                "signals_followed": followed,
                "signals_missed": missed,
                "follow_rate": round(follow_rate, 1),
                "potential_gain": round(signal_stats["total_pnl_percent"], 2) if signal_stats["total_pnl_percent"] > 0 else 0
            },
            "period_days": days
        }
    
    def generate_monthly_snapshot(self, db: Session, user_id: int, period: str) -> PerformanceSnapshot:
        """Generate monthly performance snapshot"""
        # Parse period (e.g., "2024-01")
        year, month = map(int, period.split("-"))
        start = datetime(year, month, 1, tzinfo=timezone.utc)
        if month == 12:
            end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end = datetime(year, month + 1, 1, tzinfo=timezone.utc)
        
        # User trades for period
        trades = db.query(UserTrade).filter(
            UserTrade.user_id == user_id,
            UserTrade.executed_at >= start,
            UserTrade.executed_at < end
        ).all()
        
        # Signals for period
        signals = db.query(SignalHistory).filter(
            SignalHistory.signal_time >= start,
            SignalHistory.signal_time < end,
            SignalHistory.outcome.isnot(None)
        ).all()
        
        signal_wins = [s for s in signals if s.outcome == "win"]
        signal_losses = [s for s in signals if s.outcome == "loss"]
        
        snapshot = PerformanceSnapshot(
            user_id=user_id,
            period=period,
            user_trades=len(trades),
            signal_count=len(signals),
            signal_wins=len(signal_wins),
            signal_losses=len(signal_losses),
            signal_pnl_percent=sum(s.pnl_percent for s in signals)
        )
        
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return snapshot


performance_service = PerformanceService()
