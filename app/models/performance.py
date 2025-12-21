"""
Performance Tracking Models
Track user trades and compare against ELUXRAJ signals
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from datetime import datetime, timezone
from app.db.base import Base


class UserTrade(Base):
    """User's actual trades"""
    __tablename__ = "user_trades"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Trade details
    symbol = Column(String(20), nullable=False)
    asset_type = Column(String(20), default="crypto")  # crypto, stock
    side = Column(String(10), nullable=False)  # buy, sell
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    
    # Source
    source = Column(String(50), default="manual")  # manual, signal, auto
    signal_id = Column(Integer, ForeignKey("signal_history.id"), nullable=True)
    
    # Timestamps
    executed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SignalHistory(Base):
    """Historical ELUXRAJ signals for comparison"""
    __tablename__ = "signal_history"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Signal details
    symbol = Column(String(20), nullable=False, index=True)
    asset_type = Column(String(20), default="crypto")
    signal_type = Column(String(20), nullable=False)  # buy, sell, hold
    
    # Prices
    entry_price = Column(Float, nullable=False)
    target_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    
    # Outcome (filled later)
    exit_price = Column(Float, nullable=True)
    outcome = Column(String(20), nullable=True)  # win, loss, open
    pnl_percent = Column(Float, nullable=True)
    
    # Metadata
    confidence = Column(Float, default=70.0)
    reasoning = Column(Text, nullable=True)
    
    # Timestamps
    signal_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    closed_at = Column(DateTime, nullable=True)


class PerformanceSnapshot(Base):
    """Monthly performance snapshots"""
    __tablename__ = "performance_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Period
    period = Column(String(20), nullable=False)  # "2024-01", "2024-02"
    
    # User stats
    user_trades = Column(Integer, default=0)
    user_wins = Column(Integer, default=0)
    user_losses = Column(Integer, default=0)
    user_pnl_percent = Column(Float, default=0.0)
    
    # ELUXRAJ stats (if user followed all signals)
    signal_count = Column(Integer, default=0)
    signal_wins = Column(Integer, default=0)
    signal_losses = Column(Integer, default=0)
    signal_pnl_percent = Column(Float, default=0.0)
    
    # Comparison
    followed_signals = Column(Integer, default=0)
    missed_signals = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
