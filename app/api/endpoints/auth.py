from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token, UserUpdate
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.deps import get_current_user
from app.core.logging import logger

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        logger.info(f"Registering user: {user_data.email}")
        
        existing_user = db.query(User).filter(User.email == user_data.email.lower()).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        hashed_pw = get_password_hash(user_data.password)
        logger.info("Password hashed successfully")
        
        user = User(
            email=user_data.email.lower(),
            hashed_password=hashed_pw,
            full_name=user_data.full_name,
            subscription_tier="free",
            email_alerts=True,
            push_alerts=True,
            is_active=True,
            is_verified=False
        )
        
        db.add(user)
        logger.info("User added to session")
        
        db.commit()
        logger.info("User committed to database")
        
        db.refresh(user)
        logger.info(f"User created with ID: {user.id}")
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login and get access token"""
    try:
        user = db.query(User).filter(User.email == credentials.email.lower()).first()
        
        if not user or not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        user.last_login = datetime.utcnow()
        db.commit()
        
        access_token = create_access_token(subject=user.id)
        
        return Token(access_token=access_token)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user

@router.patch("/me", response_model=UserResponse)
async def update_me(
    updates: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update current user profile"""
    if updates.full_name is not None:
        current_user.full_name = updates.full_name
    if updates.email_alerts is not None:
        current_user.email_alerts = updates.email_alerts
    if updates.push_alerts is not None:
        current_user.push_alerts = updates.push_alerts
    
    db.commit()
    db.refresh(current_user)
    return current_user
