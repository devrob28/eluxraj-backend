"""Apple Push Notification Service (APNs)"""
import jwt
import time
import httpx
from typing import Optional
from app.core.config import settings
from app.core.logging import logger


class APNsService:
    """Send push notifications to iOS devices via APNs HTTP/2"""
    
    def __init__(self):
        self.key_id = getattr(settings, 'APNS_KEY_ID', None)
        self.team_id = getattr(settings, 'APNS_TEAM_ID', None)
        self.bundle_id = getattr(settings, 'APNS_BUNDLE_ID', 'com.eluxraj.app')
        self.key_path = getattr(settings, 'APNS_KEY_PATH', None)
        self.use_sandbox = getattr(settings, 'APNS_SANDBOX', True)
        self._token = None
        self._token_time = 0
    
    @property
    def apns_url(self):
        if self.use_sandbox:
            return "https://api.sandbox.push.apple.com"
        return "https://api.push.apple.com"
    
    def _get_auth_token(self) -> Optional[str]:
        """Generate JWT token for APNs (valid for 1 hour)"""
        if not all([self.key_id, self.team_id, self.key_path]):
            logger.warning("APNs not configured - missing credentials")
            return None
        
        # Reuse token if less than 50 minutes old
        if self._token and (time.time() - self._token_time) < 3000:
            return self._token
        
        try:
            with open(self.key_path, 'r') as f:
                private_key = f.read()
            
            self._token = jwt.encode(
                {
                    "iss": self.team_id,
                    "iat": int(time.time())
                },
                private_key,
                algorithm="ES256",
                headers={
                    "alg": "ES256",
                    "kid": self.key_id
                }
            )
            self._token_time = time.time()
            return self._token
        except Exception as e:
            logger.error(f"APNs token generation failed: {e}")
            return None
    
    async def send_notification(
        self,
        device_token: str,
        title: str,
        body: str,
        badge: int = 1,
        sound: str = "default",
        data: dict = None
    ) -> bool:
        """Send push notification to iOS device"""
        if not device_token:
            return False
        
        auth_token = self._get_auth_token()
        if not auth_token:
            logger.warning("APNs auth token not available")
            return False
        
        url = f"{self.apns_url}/3/device/{device_token}"
        
        payload = {
            "aps": {
                "alert": {
                    "title": title,
                    "body": body
                },
                "badge": badge,
                "sound": sound
            }
        }
        
        if data:
            payload["data"] = data
        
        headers = {
            "authorization": f"bearer {auth_token}",
            "apns-topic": self.bundle_id,
            "apns-push-type": "alert",
            "apns-priority": "10"
        }
        
        try:
            async with httpx.AsyncClient(http2=True) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info(f"APNs notification sent to {device_token[:20]}...")
                    return True
                else:
                    logger.error(f"APNs error {response.status_code}: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"APNs send error: {e}")
            return False
    
    async def send_trade_alert(
        self,
        device_token: str,
        asset: str,
        action: str,
        price: float,
        confidence: int = None
    ) -> bool:
        """Send trade alert notification"""
        title = f"🎯 {asset} Trade Alert"
        body = f"{action} signal at ${price:,.2f}"
        if confidence:
            body += f" ({confidence}% confidence)"
        
        return await self.send_notification(
            device_token=device_token,
            title=title,
            body=body,
            data={"asset": asset, "action": action, "price": price}
        )
    
    async def send_price_alert(
        self,
        device_token: str,
        asset: str,
        current_price: float,
        threshold: float,
        direction: str
    ) -> bool:
        """Send price alert notification"""
        title = f"🚨 {asset} Price Alert"
        body = f"Now ${current_price:,.2f} ({direction} ${threshold:,.2f})"
        
        return await self.send_notification(
            device_token=device_token,
            title=title,
            body=body,
            data={"asset": asset, "price": current_price, "threshold": threshold}
        )
    
    async def send_whale_alert(
        self,
        device_token: str,
        asset: str,
        amount: float,
        usd_value: float,
        direction: str
    ) -> bool:
        """Send whale movement alert"""
        title = f"🐳 Whale Alert: {asset}"
        body = f"{direction}: {amount:,.0f} {asset} (${usd_value/1e6:.1f}M)"
        
        return await self.send_notification(
            device_token=device_token,
            title=title,
            body=body,
            data={"asset": asset, "amount": amount, "usd_value": usd_value}
        )


apns_service = APNsService()
