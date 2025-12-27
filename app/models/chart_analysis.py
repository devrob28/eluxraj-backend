"""Chart Analysis Model"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from app.db.base import Base


class ChartAnalysis(Base):
    """Store chart analysis history"""
    __tablename__ = "chart_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Input
    asset = Column(String(50), nullable=False)
    timeframe = Column(String(20), nullable=False)
    
    # Analysis results
    pattern_detected = Column(String(100))
    market_structure = Column(String(50))
    key_levels = Column(JSON)  # {support: [], resistance: []}
    
    trade_recommendation = Column(String(20))  # long, short, no_trade, wait
    trade_setup = Column(JSON)  # {entry, stop_loss, tp1, tp2, tp3, risk_reward}
    
    bullish_scenarios = Column(JSON)
    bearish_scenarios = Column(JSON)
    invalidation_conditions = Column(JSON)
    
    confidence_score = Column(Float, default=0)
    reasoning = Column(Text)
    
    # Metadata
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
