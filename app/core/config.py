from pydantic_settings import BaseSettings
from typing import Optional
import secrets
import os

class Settings(BaseSettings):
    # App
    APP_NAME: str = "ELUXRAJ API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 365 * 100  # 100 years
    ALGORITHM: str = "HS256"
    
    # Database - Railway provides DATABASE_URL automatically
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./eluxraj.db")
    
    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    # External APIs
    COINGECKO_API_KEY: Optional[str] = os.getenv("COINGECKO_API_KEY")
    
    # Email
    SENDGRID_API_KEY: Optional[str] = os.getenv("SENDGRID_API_KEY")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "signals@eluxraj.ai")
    
    # Push Notifications
    VAPID_PRIVATE_KEY: Optional[str] = os.getenv("VAPID_PRIVATE_KEY")
    VAPID_PUBLIC_KEY: Optional[str] = os.getenv("VAPID_PUBLIC_KEY")
    
    # APNs (iOS Push)
    APNS_KEY_ID: Optional[str] = os.getenv("APNS_KEY_ID")
    APNS_TEAM_ID: Optional[str] = os.getenv("APNS_TEAM_ID")
    APNS_BUNDLE_ID: str = os.getenv("APNS_BUNDLE_ID", "com.eluxraj.app")
    APNS_KEY_PATH: Optional[str] = os.getenv("APNS_KEY_PATH")
    APNS_SANDBOX: bool = os.getenv("APNS_SANDBOX", "true").lower() == "true"
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

