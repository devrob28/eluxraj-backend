from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import decode_token
from app.models.user import User

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    user_id = decode_token(token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    return current_user

def require_subscription(min_tier: str):
    """Dependency to require minimum subscription tier"""
    tier_levels = {
        "free": 0,
        "pro": 1,
        "elite": 2
    }
    
    async def check_subscription(
        current_user: User = Depends(get_current_user)
    ) -> User:
        user_level = tier_levels.get(current_user.subscription_tier, 0)
        required_level = tier_levels.get(min_tier, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires {min_tier} subscription or higher"
            )
        return current_user
    
    return check_subscription


async def require_elite(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require Elite subscription tier"""
    if current_user.subscription_tier not in ['elite', 'pro']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Elite subscription required"
        )
    return current_user


async def require_pro(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require Pro or Elite subscription tier"""
    if current_user.subscription_tier not in ['elite', 'pro']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Pro subscription required"
        )
    return current_user
