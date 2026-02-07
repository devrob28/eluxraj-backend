"""
Signal Model - Trading signals from Lambda scanner
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.db.base import Base


class Signal(Base):
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Asset info
    symbol = Column(String(20), nullable=False, index=True)
    pair = Column(String(30))
    asset_type = Column(String(20), default="stock")  # stock, crypto, forex
    timeframe = Column(String(10))  # 15m, 1h, 4h, 1d
    
    # Signal details
    signal_type = Column(String(10), nullable=False)  # buy, sell
    oracle_score = Column(Integer, default=0)  # confidence 0-100
    
    # Trade setup
    entry_price = Column(Float)
    stop_loss = Column(Float)
    target_price = Column(Float)  # TP1
    target_2 = Column(Float)  # TP2
    target_3 = Column(Float)  # TP3
    risk_reward = Column(Float)
    
    # Analysis
    pattern = Column(String(100))
    catalyst = Column(String(255))
    urgency = Column(String(20), default="medium")  # high, medium, low
    reasoning = Column(Text)
    
    # Status tracking
    status = Column(String(20), default="active")  # active, hit_target, hit_stop, expired, cancelled
    source = Column(String(50), default="lambda_scanner")  # lambda_scanner, manual, user
    
    # Outcome tracking
    outcome_price = Column(Float)
    outcome_pnl_percent = Column(Float)
    outcome_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<Signal {self.symbol} {self.signal_type} @ {self.oracle_score}%>"
