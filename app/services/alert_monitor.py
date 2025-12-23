"""
Alert Monitor Service
Background job to check prices and trigger alerts
"""
import httpx
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.core.logging import logger


class AlertMonitor:
    """Monitor prices and trigger alerts"""
    
    COINGECKO_API = "https://api.coingecko.com/api/v3"
    
    COIN_MAP = {
        "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
        "XRP": "ripple", "DOGE": "dogecoin", "ADA": "cardano",
        "AVAX": "avalanche-2", "LINK": "chainlink", "DOT": "polkadot",
        "MATIC": "matic-network", "LTC": "litecoin", "SHIB": "shiba-inu"
    }
    
    async def get_crypto_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Fetch current prices for multiple crypto assets"""
        prices = {}
        
        # Map symbols to CoinGecko IDs
        ids = [self.COIN_MAP.get(s.upper(), s.lower()) for s in symbols]
        ids_str = ",".join(set(ids))
        
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{self.COINGECKO_API}/simple/price",
                    params={"ids": ids_str, "vs_currencies": "usd"},
                    timeout=10.0
                )
                if r.status_code == 200:
                    data = r.json()
                    # Map back to symbols
                    for symbol in symbols:
                        coin_id = self.COIN_MAP.get(symbol.upper(), symbol.lower())
                        if coin_id in data:
                            prices[symbol.upper()] = data[coin_id].get("usd", 0)
        except Exception as e:
            logger.error(f"Price fetch error: {e}")
        
        return prices
    
    async def get_stock_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Fetch stock prices (placeholder - would use real API)"""
        # In production, use Alpha Vantage, Yahoo Finance, or similar
        # For now, return empty - stocks require API key
        return {}
    
    def check_condition(
        self,
        current_price: float,
        threshold: float,
        condition: str
    ) -> bool:
        """Check if alert condition is met"""
        if condition == "above":
            return current_price >= threshold
        elif condition == "below":
            return current_price <= threshold
        elif condition == "crosses_above":
            return current_price >= threshold
        elif condition == "crosses_below":
            return current_price <= threshold
        return False
    
    async def check_alerts(self, db: Session) -> List[Dict]:
        """Check all active alerts and return triggered ones"""
        from app.api.endpoints.alerts import AlertRule
        from app.models.user import User
        
        triggered = []
        
        # Get all active alerts
        alerts = db.query(AlertRule).filter(
            AlertRule.is_active == True,
            AlertRule.trigger_type == "price"
        ).all()
        
        if not alerts:
            return triggered
        
        # Group by asset type
        crypto_alerts = [a for a in alerts if a.asset_type == "crypto"]
        stock_alerts = [a for a in alerts if a.asset_type == "stock"]
        
        # Fetch crypto prices
        crypto_symbols = list(set(a.asset for a in crypto_alerts))
        crypto_prices = await self.get_crypto_prices(crypto_symbols) if crypto_symbols else {}
        
        # Fetch stock prices
        stock_symbols = list(set(a.asset for a in stock_alerts))
        stock_prices = await self.get_stock_prices(stock_symbols) if stock_symbols else {}
        
        prices = {**crypto_prices, **stock_prices}
        
        now = datetime.now(timezone.utc)
        
        for alert in alerts:
            current_price = prices.get(alert.asset.upper())
            if not current_price:
                continue
            
            # Check cooldown
            if alert.last_triggered:
                cooldown_end = alert.last_triggered + timedelta(minutes=alert.cooldown_minutes)
                if now < cooldown_end:
                    continue
            
            # Check condition
            if self.check_condition(current_price, alert.threshold, alert.condition):
                # Get user info
                user = db.query(User).filter(User.id == alert.user_id).first()
                if not user:
                    continue
                
                triggered.append({
                    "alert_id": alert.id,
                    "user_id": alert.user_id,
                    "user_email": user.email,
                    "user_phone": getattr(user, 'phone', None),
                    "alert_name": alert.name,
                    "asset": alert.asset,
                    "condition": alert.condition,
                    "threshold": alert.threshold,
                    "current_price": current_price,
                    "notify_email": alert.notify_email,
                    "notify_sms": alert.notify_sms,
                    "notify_push": alert.notify_push,
                    "webhook_url": alert.webhook_url
                })
                
                # Update alert state
                alert.last_triggered = now
                alert.trigger_count += 1
        
        db.commit()
        return triggered
    
    async def run_alert_check(self, db: Session) -> Dict:
        """Run full alert check cycle"""
        from app.services.notification_service import notification_service
        
        logger.info("Starting alert check cycle...")
        
        triggered = await self.check_alerts(db)
        
        results = {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "triggered_count": len(triggered),
            "notifications_sent": []
        }
        
        for alert in triggered:
            notification_result = await notification_service.send_alert_notification(
                user_email=alert["user_email"],
                user_phone=alert.get("user_phone"),
                alert_name=alert["alert_name"],
                asset=alert["asset"],
                condition=alert["condition"],
                threshold=alert["threshold"],
                current_price=alert["current_price"],
                notify_email=alert["notify_email"],
                notify_sms=alert["notify_sms"],
                notify_push=alert["notify_push"],
                webhook_url=alert.get("webhook_url")
            )
            
            results["notifications_sent"].append({
                "alert_id": alert["alert_id"],
                "asset": alert["asset"],
                "result": notification_result
            })
        
        logger.info(f"Alert check complete. Triggered: {len(triggered)}")
        return results


alert_monitor = AlertMonitor()
