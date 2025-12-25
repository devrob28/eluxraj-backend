"""Web Push Service"""
import json
from pywebpush import webpush, WebPushException
from app.core.config import settings
from app.core.logging import logger

class PushService:
    def __init__(self):
        self.private_key = getattr(settings, 'VAPID_PRIVATE_KEY', None)
        self.public_key = getattr(settings, 'VAPID_PUBLIC_KEY', None)
    
    def send_push(self, subscription: dict, title: str, body: str, url: str = None) -> bool:
        if not self.private_key or not subscription:
            return False
        
        try:
            payload = json.dumps({
                "title": title,
                "body": body,
                "icon": "/icon-192.png",
                "badge": "/badge-72.png",
                "url": url or "https://eluxraj.ai/dashboard.html"
            })
            
            webpush(
                subscription_info=subscription,
                data=payload,
                vapid_private_key=self.private_key,
                vapid_claims={"sub": "mailto:eluxraj@gmail.com"}
            )
            logger.info("Push notification sent")
            return True
        except WebPushException as e:
            logger.error(f"Push failed: {e}")
            if e.response and e.response.status_code == 410:
                logger.info("Subscription expired")
            return False
        except Exception as e:
            logger.error(f"Push error: {e}")
            return False

push_service = PushService()
