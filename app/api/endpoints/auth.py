from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
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
            subscription_tier="lite",
            email_alerts=True,
            push_alerts=True,
            is_active=True,
            is_verified=True
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


# Password Reset Endpoints
import secrets
from datetime import timedelta

# In-memory store for reset tokens (in production, use Redis or database)
_reset_tokens = {}

@router.post("/forgot-password")
async def forgot_password(email: str, db: Session = Depends(get_db)):
    """Request password reset"""
    user = db.query(User).filter(User.email == email.lower()).first()
    
    # Always return success to prevent email enumeration
    if not user:
        return {"ok": True, "message": "If that email exists, a reset link has been sent"}
    
    # Generate reset token
    token = secrets.token_urlsafe(32)
    _reset_tokens[token] = {"user_id": user.id, "expires": datetime.utcnow() + timedelta(hours=1)}
    
    # TODO: Send email with reset link
    # For now, log the token
    logger.info(f"Password reset token for {email}: {token}")
    
    return {"ok": True, "message": "If that email exists, a reset link has been sent"}

@router.post("/reset-password")
async def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
    """Reset password with token"""
    if token not in _reset_tokens:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    token_data = _reset_tokens[token]
    if datetime.utcnow() > token_data["expires"]:
        del _reset_tokens[token]
        raise HTTPException(status_code=400, detail="Reset token has expired")
    
    user = db.query(User).filter(User.id == token_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    del _reset_tokens[token]
    
    return {"ok": True, "message": "Password has been reset successfully"}

@router.post("/admin-reset-password")
async def admin_reset_password(email: str, new_password: str, db: Session = Depends(get_db)):
    """Admin endpoint to reset any user's password (TEMPORARY - remove in production)"""
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    logger.info(f"Password reset for {email} by admin")
    return {"ok": True, "message": f"Password reset for {email}"}


class UpdatePhoneRequest(BaseModel):
    phone: str


@router.put("/phone")
async def update_phone(req: UpdatePhoneRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Update user phone number for SMS alerts"""
    # Clean phone number
    phone = req.phone.replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
    if not phone.startswith("+"):
        phone = "+1" + phone  # Default to US
    
    user.phone = phone
    db.commit()
    
    return {"ok": True, "message": "Phone number updated", "phone": phone}


@router.get("/phone")
async def get_phone(user=Depends(get_current_user)):
    """Get user phone number"""
    return {"ok": True, "phone": getattr(user, 'phone', None)}


# Password Reset Models
class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Send password reset email"""
    import secrets
    import os
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    
    email = request.email.lower()
    user = db.query(User).filter(User.email == email).first()
    
    # Always return success to prevent email enumeration
    if not user:
        logger.info(f"Password reset requested for non-existent email: {email}")
        return {"message": "If an account exists with this email, a reset link has been sent."}
    
    # Generate reset token (valid for 1 hour)
    reset_token = secrets.token_urlsafe(32)
    
    # Store token in user record (we'll add this field)
    user.reset_token = reset_token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    
    # Send email
    reset_url = f"https://eluxraj.ai/reset-password.html?token={reset_token}"
    
    try:
        sg_api_key = os.getenv("SENDGRID_API_KEY")
        if sg_api_key:
            message = Mail(
                from_email=os.getenv("FROM_EMAIL", "eluxraj@gmail.com"),
                to_emails=email,
                subject="Reset Your ELUXRAJ Password",
                html_content=f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #7c3aed;">Reset Your Password</h2>
                    <p>You requested a password reset for your ELUXRAJ account.</p>
                    <p>Click the button below to reset your password. This link expires in 1 hour.</p>
                    <a href="{reset_url}" style="display: inline-block; background: linear-gradient(135deg, #7c3aed, #06b6d4); color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; margin: 20px 0;">Reset Password</a>
                    <p style="color: #666; font-size: 14px;">If you didn't request this, you can safely ignore this email.</p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="color: #999; font-size: 12px;">© 2025 ELUXRAJ™. All rights reserved.</p>
                </div>
                """
            )
            sg = SendGridAPIClient(sg_api_key)
            sg.send(message)
            logger.info(f"Password reset email sent to {email}")
        else:
            logger.warning("SendGrid API key not configured")
    except Exception as e:
        logger.error(f"Failed to send reset email: {e}")
    
    return {"message": "If an account exists with this email, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using token"""
    
    user = db.query(User).filter(User.reset_token == request.token).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    if user.reset_token_expires and user.reset_token_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset token has expired. Please request a new one.")
    
    # Validate password
    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    # Update password
    user.hashed_password = get_password_hash(request.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    
    logger.info(f"Password reset successful for user {user.id}")
    
    return {"message": "Password reset successful. You can now log in with your new password."}
