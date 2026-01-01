"""Push Notification Endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.db.session import get_db
from app.core.deps import get_current_user
from app.core.config import settings
from app.core.logging import logger

router = APIRouter()

class PushSubscription(BaseModel):
    endpoint: str
    keys: dict

@router.get("/vapid-key")
async def get_vapid_key():
    """Get public VAPID key for push subscription"""
    key = getattr(settings, 'VAPID_PUBLIC_KEY', None)
    if not key:
        raise HTTPException(status_code=500, detail="Push not configured")
    return {"publicKey": key}

@router.post("/subscribe")
async def subscribe_push(
    subscription: PushSubscription,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save push subscription for user"""
    user.push_subscription = {
        "endpoint": subscription.endpoint,
        "keys": subscription.keys
    }
    db.commit()
    logger.info(f"Push subscription saved for user {user.id}")
    return {"ok": True, "message": "Subscribed to push notifications"}

@router.delete("/unsubscribe")
async def unsubscribe_push(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Remove push subscription"""
    user.push_subscription = None
    db.commit()
    return {"ok": True, "message": "Unsubscribed from push notifications"}


class DeviceTokenRequest(BaseModel):
    deviceToken: str
    platform: str = "ios"

@router.post("/device-token")
async def register_device_token(
    request: DeviceTokenRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register iOS device token for APNs"""
    user.device_token = request.deviceToken
    db.commit()
    logger.info(f"iOS device token registered for user {user.id}")
    return {"ok": True, "message": "Device token registered"}

@router.delete("/device-token")
async def remove_device_token(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove iOS device token"""
    user.device_token = None
    db.commit()
    return {"ok": True, "message": "Device token removed"}
