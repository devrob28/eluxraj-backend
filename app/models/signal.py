from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, Boolean
from sqlalchemy.sql import func
from app.db.base import Base

class Signal(Base):
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_type = Column(String(20), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    pair = Column(String(20), nullable=False)
    signal_type = Column(String(10), nullable=False)
    oracle_score = Column(Integer, nullable=False)
    confidence = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    target_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    risk_reward_ratio = Column(Float, nullable=False)
    position_size_suggestion = Column(Float, nullable=True)
    reasoning_summary = Column(Text, nullable=False)
    reasoning_factors = Column(JSON, nullable=False)
    model_version = Column(String(50), nullable=False)
    input_snapshot = Column(JSON, nullable=False)
    data_sources = Column(JSON, nullable=False)
    timeframe = Column(String(20), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), default="active")
    outcome_price = Column(Float, nullable=True)
    outcome_pnl_percent = Column(Float, nullable=True)
    outcome_at = Column(DateTime(timezone=True), nullable=True)
    is_delivered = Column(Boolean, default=False)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

class SignalDelivery(Base):
    __tablename__ = "signal_deliveries"
    
    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    delivery_method = Column(String(20), nullable=False)
    delivered_at = Column(DateTime(timezone=True), server_default=func.now())
    opened_at = Column(DateTime(timezone=True), nullable=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True)
