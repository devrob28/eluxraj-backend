from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)  # For SMS alerts
    push_subscription = Column(JSON, nullable=True)  # Web push subscription
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    
    # Subscription
    subscription_tier = Column(String(20), default="lite")
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    subscription_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Preferences
    email_alerts = Column(Boolean, default=True)
    push_alerts = Column(Boolean, default=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Password Reset
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
