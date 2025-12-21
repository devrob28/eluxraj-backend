"""
Brokerage API - Connect and trade via Alpaca & Coinbase
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.brokerage import BrokerageConnection
from app.services.alpaca_service import alpaca_service
from app.services.coinbase_service import coinbase_service

router = APIRouter()


class ConnectRequest(BaseModel):
    brokerage: str  # "alpaca" or "coinbase"
    api_key: str
    api_secret: str
    paper_trading: bool = True


class TradeRequest(BaseModel):
    brokerage: str
    symbol: str  # "AAPL" for stocks, "BTC-USD" for crypto
    side: str  # "buy" or "sell"
    amount: float  # USD amount to trade
    order_type: str = "market"


class SettingsRequest(BaseModel):
    auto_trade: bool = False
    max_trade_size: int = 100


@router.get("/connections")
async def get_connections(user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user's connected brokerages"""
    connections = db.query(BrokerageConnection).filter(
        BrokerageConnection.user_id == user.id,
        BrokerageConnection.is_active == True
    ).all()
    
    return {
        "ok": True,
        "connections": [
            {
                "id": c.id,
                "brokerage": c.brokerage,
                "paper_trading": c.paper_trading,
                "auto_trade": c.auto_trade,
                "max_trade_size": c.max_trade_size,
                "connected_at": c.created_at.isoformat()
            }
            for c in connections
        ]
    }


@router.post("/connect")
async def connect_brokerage(req: ConnectRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Connect a brokerage account"""
    if req.brokerage not in ["alpaca", "coinbase"]:
        raise HTTPException(status_code=400, detail="Invalid brokerage. Use 'alpaca' or 'coinbase'")
    
    # Verify credentials work
    if req.brokerage == "alpaca":
        account = await alpaca_service.get_account(req.api_key, req.api_secret, req.paper_trading)
        if not account:
            raise HTTPException(status_code=400, detail="Invalid Alpaca credentials")
    else:
        accounts = await coinbase_service.get_accounts(req.api_key, req.api_secret)
        if not accounts and accounts != []:
            raise HTTPException(status_code=400, detail="Invalid Coinbase credentials")
    
    # Check if already connected
    existing = db.query(BrokerageConnection).filter(
        BrokerageConnection.user_id == user.id,
        BrokerageConnection.brokerage == req.brokerage,
        BrokerageConnection.is_active == True
    ).first()
    
    if existing:
        # Update existing connection
        existing.api_key = req.api_key
        existing.api_secret = req.api_secret
        existing.paper_trading = req.paper_trading
        db.commit()
        return {"ok": True, "message": f"{req.brokerage.title()} connection updated"}
    
    # Create new connection
    connection = BrokerageConnection(
        user_id=user.id,
        brokerage=req.brokerage,
        api_key=req.api_key,
        api_secret=req.api_secret,
        paper_trading=req.paper_trading
    )
    db.add(connection)
    db.commit()
    
    return {"ok": True, "message": f"{req.brokerage.title()} connected successfully"}


@router.delete("/disconnect/{brokerage}")
async def disconnect_brokerage(brokerage: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Disconnect a brokerage"""
    connection = db.query(BrokerageConnection).filter(
        BrokerageConnection.user_id == user.id,
        BrokerageConnection.brokerage == brokerage,
        BrokerageConnection.is_active == True
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    connection.is_active = False
    db.commit()
    
    return {"ok": True, "message": f"{brokerage.title()} disconnected"}


@router.get("/account/{brokerage}")
async def get_account(brokerage: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Get brokerage account info"""
    connection = db.query(BrokerageConnection).filter(
        BrokerageConnection.user_id == user.id,
        BrokerageConnection.brokerage == brokerage,
        BrokerageConnection.is_active == True
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Brokerage not connected")
    
    if brokerage == "alpaca":
        account = await alpaca_service.get_account(
            connection.api_key, 
            connection.api_secret, 
            connection.paper_trading
        )
        positions = await alpaca_service.get_positions(
            connection.api_key,
            connection.api_secret,
            connection.paper_trading
        )
        return {"ok": True, "account": account, "positions": positions}
    
    elif brokerage == "coinbase":
        portfolio = await coinbase_service.get_portfolio_value(
            connection.api_key,
            connection.api_secret
        )
        return {"ok": True, "portfolio": portfolio}
    
    raise HTTPException(status_code=400, detail="Invalid brokerage")


@router.post("/trade")
async def place_trade(req: TradeRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Execute a trade"""
    connection = db.query(BrokerageConnection).filter(
        BrokerageConnection.user_id == user.id,
        BrokerageConnection.brokerage == req.brokerage,
        BrokerageConnection.is_active == True
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Brokerage not connected")
    
    # Check trade size limit
    if req.amount > connection.max_trade_size:
        raise HTTPException(
            status_code=400, 
            detail=f"Trade exceeds max size of ${connection.max_trade_size}"
        )
    
    if req.brokerage == "alpaca":
        # Get current price to calculate shares
        # For simplicity, use market order with notional (dollar amount)
        result = await alpaca_service.place_order(
            api_key=connection.api_key,
            api_secret=connection.api_secret,
            symbol=req.symbol,
            qty=1,  # Will be replaced with notional
            side=req.side,
            order_type=req.order_type,
            paper=connection.paper_trading
        )
    
    elif req.brokerage == "coinbase":
        result = await coinbase_service.place_order(
            api_key=connection.api_key,
            api_secret=connection.api_secret,
            product_id=req.symbol,
            side=req.side.upper(),
            quote_size=req.amount,
            order_type=req.order_type
        )
    
    else:
        raise HTTPException(status_code=400, detail="Invalid brokerage")
    
    # Update last used
    connection.last_used = datetime.now(timezone.utc)
    db.commit()
    
    return result


@router.get("/orders/{brokerage}")
async def get_orders(brokerage: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Get order history"""
    connection = db.query(BrokerageConnection).filter(
        BrokerageConnection.user_id == user.id,
        BrokerageConnection.brokerage == brokerage,
        BrokerageConnection.is_active == True
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Brokerage not connected")
    
    if brokerage == "alpaca":
        orders = await alpaca_service.get_orders(
            connection.api_key,
            connection.api_secret,
            paper=connection.paper_trading
        )
    elif brokerage == "coinbase":
        orders = await coinbase_service.get_orders(
            connection.api_key,
            connection.api_secret
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid brokerage")
    
    return {"ok": True, "orders": orders}


@router.put("/settings/{brokerage}")
async def update_settings(
    brokerage: str, 
    req: SettingsRequest, 
    user=Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Update brokerage settings"""
    connection = db.query(BrokerageConnection).filter(
        BrokerageConnection.user_id == user.id,
        BrokerageConnection.brokerage == brokerage,
        BrokerageConnection.is_active == True
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Brokerage not connected")
    
    connection.auto_trade = req.auto_trade
    connection.max_trade_size = req.max_trade_size
    db.commit()
    
    return {"ok": True, "message": "Settings updated"}
