"""
Coinbase Advanced Trade Service
Connects user accounts and executes crypto trades
"""
import httpx
import hmac
import hashlib
import time
from typing import Dict, Optional, List
from datetime import datetime, timezone
from app.core.logging import logger


class CoinbaseService:
    """Coinbase Advanced Trade API integration"""
    
    BASE_URL = "https://api.coinbase.com"
    
    def _generate_signature(self, api_secret: str, timestamp: str, method: str, path: str, body: str = "") -> str:
        """Generate CB-ACCESS-SIGN header"""
        message = f"{timestamp}{method}{path}{body}"
        return hmac.new(
            api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _get_headers(self, api_key: str, api_secret: str, method: str, path: str, body: str = "") -> Dict:
        """Generate authenticated headers"""
        timestamp = str(int(time.time()))
        return {
            "CB-ACCESS-KEY": api_key,
            "CB-ACCESS-SIGN": self._generate_signature(api_secret, timestamp, method, path, body),
            "CB-ACCESS-TIMESTAMP": timestamp,
            "Content-Type": "application/json"
        }
    
    async def get_accounts(self, api_key: str, api_secret: str) -> List[Dict]:
        """Get all accounts/wallets"""
        path = "/api/v3/brokerage/accounts"
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{self.BASE_URL}{path}",
                    headers=self._get_headers(api_key, api_secret, "GET", path),
                    timeout=10.0
                )
                if r.status_code == 200:
                    data = r.json()
                    accounts = data.get("accounts", [])
                    return [
                        {
                            "id": a.get("uuid"),
                            "currency": a.get("currency"),
                            "name": a.get("name"),
                            "available": float(a.get("available_balance", {}).get("value", 0)),
                            "hold": float(a.get("hold", {}).get("value", 0))
                        }
                        for a in accounts
                        if float(a.get("available_balance", {}).get("value", 0)) > 0
                    ]
                else:
                    logger.error(f"Coinbase accounts error: {r.status_code} - {r.text}")
                    return []
        except Exception as e:
            logger.error(f"Coinbase connection error: {e}")
            return []
    
    async def get_portfolio_value(self, api_key: str, api_secret: str) -> Optional[Dict]:
        """Get total portfolio value"""
        accounts = await self.get_accounts(api_key, api_secret)
        if not accounts:
            return None
        
        total_usd = 0
        holdings = []
        
        for acc in accounts:
            if acc["currency"] == "USD":
                total_usd += acc["available"]
                holdings.append({"currency": "USD", "amount": acc["available"], "usd_value": acc["available"]})
            else:
                # Get current price
                price = await self.get_price(api_key, api_secret, f"{acc['currency']}-USD")
                if price:
                    usd_value = acc["available"] * price
                    total_usd += usd_value
                    holdings.append({
                        "currency": acc["currency"],
                        "amount": acc["available"],
                        "price": price,
                        "usd_value": usd_value
                    })
        
        return {
            "total_usd": total_usd,
            "holdings": holdings
        }
    
    async def get_price(self, api_key: str, api_secret: str, product_id: str) -> Optional[float]:
        """Get current price for a product"""
        path = f"/api/v3/brokerage/products/{product_id}"
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{self.BASE_URL}{path}",
                    headers=self._get_headers(api_key, api_secret, "GET", path),
                    timeout=10.0
                )
                if r.status_code == 200:
                    data = r.json()
                    return float(data.get("price", 0))
                return None
        except Exception as e:
            logger.error(f"Coinbase price error: {e}")
            return None
    
    async def place_order(
        self,
        api_key: str,
        api_secret: str,
        product_id: str,  # e.g., "BTC-USD"
        side: str,  # "BUY" or "SELL"
        size: float = None,  # Base currency amount (e.g., 0.001 BTC)
        quote_size: float = None,  # Quote currency amount (e.g., $100 USD)
        order_type: str = "market"
    ) -> Optional[Dict]:
        """Place a trade order"""
        import uuid
        
        path = "/api/v3/brokerage/orders"
        
        order_config = {}
        if order_type == "market":
            if quote_size:
                order_config = {"market_market_ioc": {"quote_size": str(quote_size)}}
            elif size:
                order_config = {"market_market_ioc": {"base_size": str(size)}}
        
        body_dict = {
            "client_order_id": str(uuid.uuid4()),
            "product_id": product_id.upper(),
            "side": side.upper(),
            "order_configuration": order_config
        }
        
        import json
        body = json.dumps(body_dict)
        
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{self.BASE_URL}{path}",
                    headers=self._get_headers(api_key, api_secret, "POST", path, body),
                    content=body,
                    timeout=10.0
                )
                
                if r.status_code in [200, 201]:
                    data = r.json()
                    order = data.get("success_response", {})
                    logger.info(f"Coinbase order placed: {side} {product_id}")
                    return {
                        "ok": True,
                        "order_id": order.get("order_id"),
                        "product_id": order.get("product_id"),
                        "side": order.get("side"),
                        "status": "pending"
                    }
                else:
                    error = r.json()
                    logger.error(f"Coinbase order error: {r.status_code} - {error}")
                    return {
                        "ok": False,
                        "error": error.get("error_response", {}).get("message", "Order failed")
                    }
        except Exception as e:
            logger.error(f"Coinbase order exception: {e}")
            return {"ok": False, "error": str(e)}
    
    async def get_orders(self, api_key: str, api_secret: str, product_id: str = None) -> List[Dict]:
        """Get orders history"""
        path = "/api/v3/brokerage/orders/historical/batch"
        try:
            async with httpx.AsyncClient() as client:
                params = {"limit": "50"}
                if product_id:
                    params["product_id"] = product_id
                
                r = await client.get(
                    f"{self.BASE_URL}{path}",
                    params=params,
                    headers=self._get_headers(api_key, api_secret, "GET", path),
                    timeout=10.0
                )
                if r.status_code == 200:
                    data = r.json()
                    orders = data.get("orders", [])
                    return [
                        {
                            "id": o.get("order_id"),
                            "product_id": o.get("product_id"),
                            "side": o.get("side"),
                            "status": o.get("status"),
                            "filled_size": o.get("filled_size"),
                            "filled_value": o.get("filled_value"),
                            "created_at": o.get("created_time")
                        }
                        for o in orders
                    ]
                return []
        except Exception as e:
            logger.error(f"Coinbase orders error: {e}")
            return []
    
    async def cancel_order(self, api_key: str, api_secret: str, order_id: str) -> bool:
        """Cancel an open order"""
        path = "/api/v3/brokerage/orders/batch_cancel"
        body = {"order_ids": [order_id]}
        
        import json
        body_str = json.dumps(body)
        
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{self.BASE_URL}{path}",
                    headers=self._get_headers(api_key, api_secret, "POST", path, body_str),
                    content=body_str,
                    timeout=10.0
                )
                return r.status_code == 200
        except Exception as e:
            logger.error(f"Coinbase cancel error: {e}")
            return False


coinbase_service = CoinbaseService()
