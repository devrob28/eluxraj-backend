"""
Alpaca Brokerage Service
Connects user accounts and executes stock trades
"""
import httpx
from typing import Dict, Optional, List
from datetime import datetime, timezone
from app.core.config import settings
from app.core.logging import logger


class AlpacaService:
    """Alpaca Trading API integration"""
    
    # Paper trading by default for safety
    PAPER_BASE = "https://paper-api.alpaca.markets"
    LIVE_BASE = "https://api.alpaca.markets"
    
    def __init__(self):
        self.client_id = getattr(settings, 'ALPACA_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'ALPACA_CLIENT_SECRET', None)
    
    def get_base_url(self, paper: bool = True) -> str:
        return self.PAPER_BASE if paper else self.LIVE_BASE
    
    async def get_account(self, api_key: str, api_secret: str, paper: bool = True) -> Optional[Dict]:
        """Get account info"""
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{self.get_base_url(paper)}/v2/account",
                    headers={
                        "APCA-API-KEY-ID": api_key,
                        "APCA-API-SECRET-KEY": api_secret
                    },
                    timeout=10.0
                )
                if r.status_code == 200:
                    data = r.json()
                    return {
                        "id": data.get("id"),
                        "status": data.get("status"),
                        "currency": data.get("currency"),
                        "cash": float(data.get("cash", 0)),
                        "portfolio_value": float(data.get("portfolio_value", 0)),
                        "buying_power": float(data.get("buying_power", 0)),
                        "equity": float(data.get("equity", 0)),
                        "pattern_day_trader": data.get("pattern_day_trader", False)
                    }
                else:
                    logger.error(f"Alpaca account error: {r.status_code} - {r.text}")
                    return None
        except Exception as e:
            logger.error(f"Alpaca connection error: {e}")
            return None
    
    async def get_positions(self, api_key: str, api_secret: str, paper: bool = True) -> List[Dict]:
        """Get current positions"""
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{self.get_base_url(paper)}/v2/positions",
                    headers={
                        "APCA-API-KEY-ID": api_key,
                        "APCA-API-SECRET-KEY": api_secret
                    },
                    timeout=10.0
                )
                if r.status_code == 200:
                    positions = r.json()
                    return [
                        {
                            "symbol": p.get("symbol"),
                            "qty": float(p.get("qty", 0)),
                            "avg_entry": float(p.get("avg_entry_price", 0)),
                            "current_price": float(p.get("current_price", 0)),
                            "market_value": float(p.get("market_value", 0)),
                            "unrealized_pl": float(p.get("unrealized_pl", 0)),
                            "unrealized_pl_pct": float(p.get("unrealized_plpc", 0)) * 100
                        }
                        for p in positions
                    ]
                return []
        except Exception as e:
            logger.error(f"Alpaca positions error: {e}")
            return []
    
    async def place_order(
        self,
        api_key: str,
        api_secret: str,
        symbol: str,
        qty: float,
        side: str,  # "buy" or "sell"
        order_type: str = "market",
        time_in_force: str = "day",
        limit_price: float = None,
        paper: bool = True
    ) -> Optional[Dict]:
        """Place a trade order"""
        try:
            order_data = {
                "symbol": symbol.upper(),
                "qty": str(qty),
                "side": side.lower(),
                "type": order_type,
                "time_in_force": time_in_force
            }
            
            if order_type == "limit" and limit_price:
                order_data["limit_price"] = str(limit_price)
            
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"{self.get_base_url(paper)}/v2/orders",
                    headers={
                        "APCA-API-KEY-ID": api_key,
                        "APCA-API-SECRET-KEY": api_secret
                    },
                    json=order_data,
                    timeout=10.0
                )
                
                if r.status_code in [200, 201]:
                    order = r.json()
                    logger.info(f"Alpaca order placed: {side} {qty} {symbol}")
                    return {
                        "ok": True,
                        "order_id": order.get("id"),
                        "status": order.get("status"),
                        "symbol": order.get("symbol"),
                        "qty": order.get("qty"),
                        "side": order.get("side"),
                        "type": order.get("type"),
                        "created_at": order.get("created_at")
                    }
                else:
                    logger.error(f"Alpaca order error: {r.status_code} - {r.text}")
                    return {"ok": False, "error": r.json().get("message", "Order failed")}
        except Exception as e:
            logger.error(f"Alpaca order exception: {e}")
            return {"ok": False, "error": str(e)}
    
    async def get_orders(self, api_key: str, api_secret: str, status: str = "all", paper: bool = True) -> List[Dict]:
        """Get orders history"""
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{self.get_base_url(paper)}/v2/orders",
                    params={"status": status, "limit": 50},
                    headers={
                        "APCA-API-KEY-ID": api_key,
                        "APCA-API-SECRET-KEY": api_secret
                    },
                    timeout=10.0
                )
                if r.status_code == 200:
                    orders = r.json()
                    return [
                        {
                            "id": o.get("id"),
                            "symbol": o.get("symbol"),
                            "qty": o.get("qty"),
                            "side": o.get("side"),
                            "type": o.get("type"),
                            "status": o.get("status"),
                            "filled_avg_price": o.get("filled_avg_price"),
                            "created_at": o.get("created_at")
                        }
                        for o in orders
                    ]
                return []
        except Exception as e:
            logger.error(f"Alpaca orders error: {e}")
            return []
    
    async def cancel_order(self, api_key: str, api_secret: str, order_id: str, paper: bool = True) -> bool:
        """Cancel an open order"""
        try:
            async with httpx.AsyncClient() as client:
                r = await client.delete(
                    f"{self.get_base_url(paper)}/v2/orders/{order_id}",
                    headers={
                        "APCA-API-KEY-ID": api_key,
                        "APCA-API-SECRET-KEY": api_secret
                    },
                    timeout=10.0
                )
                return r.status_code in [200, 204]
        except Exception as e:
            logger.error(f"Alpaca cancel error: {e}")
            return False


alpaca_service = AlpacaService()
