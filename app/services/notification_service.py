"""
Notification Service
Send alerts via Email, SMS, Push and Webhook
"""
import httpx
from typing import Optional, Dict
from datetime import datetime, timezone
from app.core.config import settings
from app.core.logging import logger
from app.services.apns_service import apns_service


class NotificationService:
    def __init__(self):
        self.sendgrid_key = getattr(settings, 'SENDGRID_API_KEY', None)
        self.twilio_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        self.twilio_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        self.twilio_phone = getattr(settings, 'TWILIO_PHONE_NUMBER', None)
        self.from_email = getattr(settings, 'FROM_EMAIL', 'eluxraj@gmail.com')
        self.vapid_private = getattr(settings, 'VAPID_PRIVATE_KEY', None)
        self.vapid_public = getattr(settings, 'VAPID_PUBLIC_KEY', None)
    
    async def send_email(self, to_email: str, subject: str, body_html: str, body_text: str = None) -> bool:
        if not self.sendgrid_key:
            logger.warning("SendGrid API key not configured")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers={
                        "Authorization": f"Bearer {self.sendgrid_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "personalizations": [{"to": [{"email": to_email}]}],
                        "from": {"email": self.from_email, "name": "ELUXRAJ Alerts"},
                        "subject": subject,
                        "content": [
                            {"type": "text/plain", "value": body_text or body_html},
                            {"type": "text/html", "value": body_html}
                        ]
                    },
                    timeout=10.0
                )
                if r.status_code in [200, 201, 202]:
                    logger.info(f"Email sent to {to_email}: {subject}")
                    return True
                else:
                    logger.error(f"SendGrid error: {r.status_code} - {r.text}")
                    return False
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return False
    
    async def send_sms(self, to_phone: str, message: str) -> bool:
        if not all([self.twilio_sid, self.twilio_token, self.twilio_phone]):
            logger.warning("Twilio credentials not configured")
            return False
        
        if not to_phone.startswith('+'):
            to_phone = '+1' + to_phone.replace('-', '').replace(' ', '')
        
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_sid}/Messages.json",
                    auth=(self.twilio_sid, self.twilio_token),
                    data={"To": to_phone, "From": self.twilio_phone, "Body": message},
                    timeout=10.0
                )
                if r.status_code in [200, 201]:
                    logger.info(f"SMS sent to {to_phone}")
                    return True
                else:
                    logger.error(f"Twilio error: {r.status_code} - {r.text}")
                    return False
        except Exception as e:
            logger.error(f"SMS send error: {e}")
            return False
    
    async def send_push(self, subscription: dict, title: str, body: str, url: str = None) -> bool:
        if not self.vapid_private or not subscription:
            return False
        
        try:
            from pywebpush import webpush, WebPushException
            import json
            
            payload = json.dumps({
                "title": title,
                "body": body,
                "icon": "/icon-192.png",
                "url": url or "https://eluxraj.ai/dashboard.html"
            })
            
            webpush(
                subscription_info=subscription,
                data=payload,
                vapid_private_key=self.vapid_private,
                vapid_claims={"sub": "mailto:eluxraj@gmail.com"}
            )
            logger.info("Push notification sent")
            return True
        except Exception as e:
            logger.error(f"Push error: {e}")
            return False
    
    async def send_webhook(self, url: str, payload: Dict) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(url, json=payload, timeout=10.0)
                return r.status_code in [200, 201, 202, 204]
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return False
    
    async def send_alert_notification(
        self,
        user_email: str,
        user_phone: Optional[str],
        alert_name: str,
        asset: str,
        condition: str,
        threshold: float,
        current_price: float,
        notify_email: bool = True,
        notify_sms: bool = False,
        notify_push: bool = True,
        push_subscription: dict = None,
        webhook_url: Optional[str] = None,
        device_token: Optional[str] = None
    ) -> Dict:
        results = {"email": False, "sms": False, "push": False, "webhook": False, "apns": False}
        
        direction = "above" if "above" in condition else "below"
        subject = f"🚨 ELUXRAJ Alert: {asset} Price Alert"
        text_message = f"ELUXRAJ Alert: {asset} is now ${current_price:,.2f} ({direction} ${threshold:,.2f})"
        
        html_message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #7c3aed, #06b6d4); padding: 20px; border-radius: 12px 12px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 24px;">🚨 Price Alert Triggered</h1>
            </div>
            <div style="background: #1a1a24; padding: 24px; border-radius: 0 0 12px 12px; color: white;">
                <h2 style="color: #7c3aed; margin-top: 0;">{alert_name}</h2>
                <div style="background: #0a0a0f; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
                    <div style="font-size: 14px; color: #9ca3af;">Asset</div>
                    <div style="font-size: 24px; font-weight: bold;">{asset}</div>
                </div>
                <div style="display: flex; gap: 12px;">
                    <div style="flex: 1; background: #0a0a0f; padding: 16px; border-radius: 8px;">
                        <div style="font-size: 14px; color: #9ca3af;">Current Price</div>
                        <div style="font-size: 20px; font-weight: bold; color: #10b981;">${current_price:,.2f}</div>
                    </div>
                    <div style="flex: 1; background: #0a0a0f; padding: 16px; border-radius: 8px;">
                        <div style="font-size: 14px; color: #9ca3af;">Your Threshold</div>
                        <div style="font-size: 20px; font-weight: bold;">${threshold:,.2f}</div>
                    </div>
                </div>
                <a href="https://eluxraj.ai/dashboard.html" style="display: block; background: linear-gradient(135deg, #7c3aed, #06b6d4); color: white; text-align: center; padding: 14px; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 20px;">View Dashboard →</a>
            </div>
        </div>
        """
        
        if notify_email and user_email:
            results["email"] = await self.send_email(user_email, subject, html_message, text_message)
        
        if notify_sms and user_phone:
            results["sms"] = await self.send_sms(user_phone, text_message)
        
        if notify_push and push_subscription:
            results["push"] = await self.send_push(push_subscription, subject, text_message)
        
        if device_token:
            results["apns"] = await apns_service.send_price_alert(
                device_token=device_token,
                asset=asset,
                current_price=current_price,
                threshold=threshold,
                direction=direction
            )
        
        if webhook_url:
            results["webhook"] = await self.send_webhook(webhook_url, {
                "alert": alert_name, "asset": asset, "condition": condition,
                "threshold": threshold, "current_price": current_price,
                "triggered_at": datetime.now(timezone.utc).isoformat()
            })
        
        return results


notification_service = NotificationService()
