from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from app.db.base import Base

class TradePlaybook(Base):
    __tablename__ = "trade_playbooks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    asset = Column(String(50), nullable=False, index=True)
    asset_type = Column(String(20), nullable=False)  # crypto, stock, forex
    timeframe = Column(String(10), nullable=False)
    
    # Core Playbook Data
    market_bias = Column(String(20), nullable=False)  # bullish, bearish, neutral
    bias_strength = Column(Float, nullable=False)  # 0-100
    
    # Trade Setup
    entry_zone_low = Column(Float, nullable=False)
    entry_zone_high = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    take_profit_1 = Column(Float, nullable=False)
    take_profit_2 = Column(Float, nullable=False)
    take_profit_3 = Column(Float, nullable=False)
    
    # Risk Metrics
    risk_reward_ratio = Column(Float, nullable=False)
    probability_score = Column(Float, nullable=False)  # 0-100
    confidence_score = Column(Float, nullable=False)  # 0-100
    
    # Scenarios (JSON arrays)
    bullish_scenarios = Column(JSON, nullable=False)  # [{name, probability, trigger, target, explanation}]
    bearish_scenarios = Column(JSON, nullable=False)
    
    # Invalidation
    invalidation_conditions = Column(JSON, nullable=False)  # [condition strings]
    invalidation_price = Column(Float, nullable=True)
    
    # Meta
    pattern_detected = Column(String(100), nullable=True)
    market_structure = Column(String(50), nullable=True)
    reasoning = Column(Text, nullable=True)
    
    # Status
    status = Column(String(20), default="active")  # active, invalidated, completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)


class ChartAnalysisV2(Base):
    __tablename__ = "chart_analyses_v2"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Input
    asset = Column(String(50), nullable=False)
    timeframe = Column(String(10), nullable=False)
    image_path = Column(String(500), nullable=True)
    
    # Detection
    pattern_detected = Column(String(100), nullable=True)
    market_structure = Column(String(50), nullable=True)  # trending_up, trending_down, ranging, breakout
    key_levels = Column(JSON, nullable=True)  # {support: [], resistance: []}
    
    # Scenarios
    bullish_scenarios = Column(JSON, nullable=False)
    bearish_scenarios = Column(JSON, nullable=False)
    
    # Trade Setup (if applicable)
    has_trade_setup = Column(String(10), default="no")  # yes, no, wait
    trade_setup = Column(JSON, nullable=True)
    
    # Scores
    confidence_score = Column(Float, nullable=False)
    risk_reward_ratio = Column(Float, nullable=True)
    
    # Meta
    reasoning = Column(Text, nullable=True)
    disclaimer = Column(Text, nullable=True)
    model_version = Column(String(50), default="v2")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
