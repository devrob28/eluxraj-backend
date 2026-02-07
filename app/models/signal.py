"""
Signal Model - Trading signals from Lambda scanner
Matches existing database schema
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.sql import func
from app.db.base import Base


class Signal(Base):
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Asset info
    symbol = Column(String(20), nullable=False, index=True)
    pair = Column(String(30))
    asset_type = Column(String(20), default="stock")
    timeframe = Column(String(10))
    
    # Signal details
    signal_type = Column(String(10), nullable=False)
    oracle_score = Column(Integer, default=0)
    confidence = Column(Float)
    
    # Trade setup
    entry_price = Column(Float)
    stop_loss = Column(Float)
    target_price = Column(Float)
    target_2 = Column(Float)
    target_3 = Column(Float)
    risk_reward = Column(Float)
    risk_reward_ratio = Column(Float)
    position_size_suggestion = Column(Float)
    
    # Analysis
    pattern = Column(String(100))
    catalyst = Column(String(255))
    urgency = Column(String(20), default="medium")
    reasoning = Column(Text)
    reasoning_summary = Column(Text)
    reasoning_factors = Column(JSON)
    
    # Metadata
    model_version = Column(String(50))
    input_snapshot = Column(JSON)
    data_sources = Column(JSON)
    source = Column(String(50), default="lambda_scanner")
    user_id = Column(Integer)
    
    # Status tracking
    status = Column(String(20), default="active")
    is_delivered = Column(Boolean, default=False)
    delivered_at = Column(DateTime(timezone=True))
    
    # Outcome tracking
    outcome_price = Column(Float)
    outcome_pnl_percent = Column(Float)
    outcome_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<Signal {self.symbol} {self.signal_type} @ {self.oracle_score}%>"
