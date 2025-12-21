"""
Brokerage Connection Model
Stores encrypted API keys for user brokerage accounts
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from datetime import datetime, timezone
from app.db.base import Base


class BrokerageConnection(Base):
    """User brokerage API connections"""
    __tablename__ = "brokerage_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Brokerage type
    brokerage = Column(String(50), nullable=False)  # "alpaca", "coinbase"
    
    # API credentials (encrypted in production)
    api_key = Column(String(500), nullable=False)
    api_secret = Column(String(500), nullable=False)
    
    # Settings
    paper_trading = Column(Boolean, default=True)  # Alpaca paper mode
    auto_trade = Column(Boolean, default=False)  # Auto-execute signals
    max_trade_size = Column(Integer, default=100)  # Max $ per trade
    
    # Status
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
