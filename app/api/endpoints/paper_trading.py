"""
ELUXRAJ Paper Trading System
Level 2: Track simulated trades based on ORACLE signals
Build performance history without real money
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel
from app.db.session import get_db, Base
from app.core.deps import get_current_user
from app.core.logging import logger

router = APIRouter()


# ============== MODELS ==============

class PaperPortfolio(Base):
    """User's paper trading portfolio"""
    __tablename__ = "paper_portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    initial_balance = Column(Float, default=100000.0)  # Start with $100k
    cash_balance = Column(Float, default=100000.0)
    total_value = Column(Float, default=100000.0)
    
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    
    total_pnl = Column(Float, default=0.0)
    total_pnl_percent = Column(Float, default=0.0)
    best_trade_pnl = Column(Float, default=0.0)
    worst_trade_pnl = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class PaperPosition(Base):
    """Open positions in paper portfolio"""
    __tablename__ = "paper_positions"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("paper_portfolios.id"), nullable=False)
    user_id = Column(Integer, nullable=False)
    
    asset = Column(String, nullable=False)
    asset_type = Column(String, default="crypto")
    side = Column(String, nullable=False)  # long, short
    
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)
    
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    
    unrealized_pnl = Column(Float, default=0.0)
    unrealized_pnl_percent = Column(Float, default=0.0)
    
    oracle_score_at_entry = Column(Integer, nullable=True)
    oracle_signal_at_entry = Column(String, nullable=True)
    
    opened_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class PaperTrade(Base):
    """Completed paper trades history"""
    __tablename__ = "paper_trades"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("paper_portfolios.id"), nullable=False)
    user_id = Column(Integer, nullable=False)
    
    asset = Column(String, nullable=False)
    asset_type = Column(String, default="crypto")
    side = Column(String, nullable=False)  # long, short
    
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=False)
    
    pnl = Column(Float, nullable=False)
    pnl_percent = Column(Float, nullable=False)
    
    oracle_score_at_entry = Column(Integer, nullable=True)
    oracle_signal_at_entry = Column(String, nullable=True)
    oracle_score_at_exit = Column(Integer, nullable=True)
    
    exit_reason = Column(String, nullable=True)  # manual, stop_loss, take_profit, oracle_signal
    
    opened_at = Column(DateTime, nullable=False)
    closed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ============== SCHEMAS ==============

class OpenPositionRequest(BaseModel):
    asset: str
    asset_type: str = "crypto"
    side: str  # long, short
    amount_usd: float  # Dollar amount to invest
    stop_loss_percent: Optional[float] = 5.0
    take_profit_percent: Optional[float] = 10.0


class ClosePositionRequest(BaseModel):
    position_id: int
    exit_reason: str = "manual"


class AutoTradeRequest(BaseModel):
    asset: str
    asset_type: str = "crypto"
    amount_usd: float = 1000.0
    follow_oracle: bool = True


# ============== HELPER FUNCTIONS ==============

async def get_current_price(asset: str, asset_type: str) -> float:
    """Get current price for an asset"""
    import httpx
    
    try:
        if asset_type == "crypto":
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"https://api.coingecko.com/api/v3/simple/price?ids={asset.lower()}&vs_currencies=usd",
                    timeout=10.0
                )
                data = resp.json()
                # Map common symbols
                symbol_map = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana"}
                coin_id = symbol_map.get(asset.upper(), asset.lower())
                return data.get(coin_id, {}).get("usd", 0)
        else:
            async with httpx.AsyncClient() as client:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{asset}?interval=1d&range=1d"
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10.0)
                data = resp.json()
                return data["chart"]["result"][0]["meta"].get("regularMarketPrice", 0)
    except Exception as e:
        logger.error(f"Price fetch error for {asset}: {e}")
        return 0


def get_or_create_portfolio(user_id: int, db: Session) -> PaperPortfolio:
    """Get or create a paper portfolio for user"""
    portfolio = db.query(PaperPortfolio).filter(PaperPortfolio.user_id == user_id).first()
    
    if not portfolio:
        portfolio = PaperPortfolio(user_id=user_id)
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
    
    return portfolio


async def update_position_prices(portfolio_id: int, db: Session):
    """Update current prices and PnL for all open positions"""
    positions = db.query(PaperPosition).filter(PaperPosition.portfolio_id == portfolio_id).all()
    
    total_position_value = 0
    
    for pos in positions:
        current_price = await get_current_price(pos.asset, pos.asset_type)
        if current_price > 0:
            pos.current_price = current_price
            
            if pos.side == "long":
                pos.unrealized_pnl = (current_price - pos.entry_price) * pos.quantity
                pos.unrealized_pnl_percent = ((current_price / pos.entry_price) - 1) * 100
            else:  # short
                pos.unrealized_pnl = (pos.entry_price - current_price) * pos.quantity
                pos.unrealized_pnl_percent = ((pos.entry_price / current_price) - 1) * 100
            
            total_position_value += current_price * pos.quantity
    
    # Update portfolio total value
    portfolio = db.query(PaperPortfolio).filter(PaperPortfolio.id == portfolio_id).first()
    if portfolio:
        portfolio.total_value = portfolio.cash_balance + total_position_value
        portfolio.total_pnl = portfolio.total_value - portfolio.initial_balance
        portfolio.total_pnl_percent = (portfolio.total_pnl / portfolio.initial_balance) * 100
    
    db.commit()


# ============== API ENDPOINTS ==============

@router.get("/portfolio")
async def get_portfolio(
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's paper trading portfolio"""
    portfolio = get_or_create_portfolio(user.id, db)
    
    # Update position prices
    await update_position_prices(portfolio.id, db)
    
    # Get open positions
    positions = db.query(PaperPosition).filter(PaperPosition.portfolio_id == portfolio.id).all()
    
    win_rate = (portfolio.winning_trades / portfolio.total_trades * 100) if portfolio.total_trades > 0 else 0
    
    return {
        "ok": True,
        "portfolio": {
            "id": portfolio.id,
            "initial_balance": portfolio.initial_balance,
            "cash_balance": round(portfolio.cash_balance, 2),
            "total_value": round(portfolio.total_value, 2),
            "total_pnl": round(portfolio.total_pnl, 2),
            "total_pnl_percent": round(portfolio.total_pnl_percent, 2),
            "total_trades": portfolio.total_trades,
            "winning_trades": portfolio.winning_trades,
            "losing_trades": portfolio.losing_trades,
            "win_rate": round(win_rate, 1),
            "best_trade": round(portfolio.best_trade_pnl, 2),
            "worst_trade": round(portfolio.worst_trade_pnl, 2)
        },
        "positions": [
            {
                "id": p.id,
                "asset": p.asset,
                "asset_type": p.asset_type,
                "side": p.side,
                "quantity": p.quantity,
                "entry_price": p.entry_price,
                "current_price": p.current_price,
                "stop_loss": p.stop_loss,
                "take_profit": p.take_profit,
                "unrealized_pnl": round(p.unrealized_pnl, 2),
                "unrealized_pnl_percent": round(p.unrealized_pnl_percent, 2),
                "oracle_score_at_entry": p.oracle_score_at_entry,
                "opened_at": p.opened_at.isoformat()
            }
            for p in positions
        ]
    }


@router.post("/position/open")
async def open_position(
    req: OpenPositionRequest,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Open a new paper trading position"""
    portfolio = get_or_create_portfolio(user.id, db)
    
    # Check if enough cash
    if req.amount_usd > portfolio.cash_balance:
        raise HTTPException(status_code=400, detail=f"Insufficient balance. Available: ${portfolio.cash_balance:.2f}")
    
    # Get current price
    current_price = await get_current_price(req.asset, req.asset_type)
    if current_price <= 0:
        raise HTTPException(status_code=400, detail=f"Could not get price for {req.asset}")
    
    # Calculate quantity
    quantity = req.amount_usd / current_price
    
    # Calculate stop loss and take profit prices
    if req.side == "long":
        stop_loss = current_price * (1 - req.stop_loss_percent / 100) if req.stop_loss_percent else None
        take_profit = current_price * (1 + req.take_profit_percent / 100) if req.take_profit_percent else None
    else:
        stop_loss = current_price * (1 + req.stop_loss_percent / 100) if req.stop_loss_percent else None
        take_profit = current_price * (1 - req.take_profit_percent / 100) if req.take_profit_percent else None
    
    # Get ORACLE signal
    oracle_score = None
    oracle_signal = None
    try:
        from app.services.oracle import oracle
        signal = await oracle.generate_signal(req.asset)
        if signal:
            oracle_score = signal.get("oracle_score")
            oracle_signal = signal.get("signal_type")
    except:
        pass
    
    # Create position
    position = PaperPosition(
        portfolio_id=portfolio.id,
        user_id=user.id,
        asset=req.asset.upper(),
        asset_type=req.asset_type,
        side=req.side,
        quantity=quantity,
        entry_price=current_price,
        current_price=current_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        oracle_score_at_entry=oracle_score,
        oracle_signal_at_entry=oracle_signal
    )
    db.add(position)
    
    # Update portfolio
    portfolio.cash_balance -= req.amount_usd
    
    db.commit()
    db.refresh(position)
    
    return {
        "ok": True,
        "position": {
            "id": position.id,
            "asset": position.asset,
            "side": position.side,
            "quantity": round(quantity, 8),
            "entry_price": current_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "oracle_score": oracle_score,
            "oracle_signal": oracle_signal
        },
        "portfolio_balance": round(portfolio.cash_balance, 2)
    }


@router.post("/position/close")
async def close_position(
    req: ClosePositionRequest,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Close a paper trading position"""
    position = db.query(PaperPosition).filter(
        PaperPosition.id == req.position_id,
        PaperPosition.user_id == user.id
    ).first()
    
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    portfolio = db.query(PaperPortfolio).filter(PaperPortfolio.id == position.portfolio_id).first()
    
    # Get current price
    current_price = await get_current_price(position.asset, position.asset_type)
    if current_price <= 0:
        current_price = position.current_price or position.entry_price
    
    # Calculate PnL
    if position.side == "long":
        pnl = (current_price - position.entry_price) * position.quantity
        pnl_percent = ((current_price / position.entry_price) - 1) * 100
    else:
        pnl = (position.entry_price - current_price) * position.quantity
        pnl_percent = ((position.entry_price / current_price) - 1) * 100
    
    # Get ORACLE score at exit
    oracle_score_exit = None
    try:
        from app.services.oracle import oracle
        signal = await oracle.generate_signal(position.asset)
        if signal:
            oracle_score_exit = signal.get("oracle_score")
    except:
        pass
    
    # Create trade record
    trade = PaperTrade(
        portfolio_id=portfolio.id,
        user_id=user.id,
        asset=position.asset,
        asset_type=position.asset_type,
        side=position.side,
        quantity=position.quantity,
        entry_price=position.entry_price,
        exit_price=current_price,
        pnl=pnl,
        pnl_percent=pnl_percent,
        oracle_score_at_entry=position.oracle_score_at_entry,
        oracle_signal_at_entry=position.oracle_signal_at_entry,
        oracle_score_at_exit=oracle_score_exit,
        exit_reason=req.exit_reason,
        opened_at=position.opened_at
    )
    db.add(trade)
    
    # Update portfolio stats
    position_value = current_price * position.quantity
    portfolio.cash_balance += position_value
    portfolio.total_trades += 1
    portfolio.total_pnl += pnl
    
    if pnl > 0:
        portfolio.winning_trades += 1
        if pnl > portfolio.best_trade_pnl:
            portfolio.best_trade_pnl = pnl
    else:
        portfolio.losing_trades += 1
        if pnl < portfolio.worst_trade_pnl:
            portfolio.worst_trade_pnl = pnl
    
    # Delete position
    db.delete(position)
    db.commit()
    db.refresh(trade)
    
    return {
        "ok": True,
        "trade": {
            "id": trade.id,
            "asset": trade.asset,
            "side": trade.side,
            "entry_price": trade.entry_price,
            "exit_price": trade.exit_price,
            "pnl": round(pnl, 2),
            "pnl_percent": round(pnl_percent, 2),
            "exit_reason": req.exit_reason
        },
        "portfolio_balance": round(portfolio.cash_balance, 2)
    }


@router.get("/trades")
async def get_trade_history(
    limit: int = 50,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get paper trading history"""
    trades = db.query(PaperTrade).filter(
        PaperTrade.user_id == user.id
    ).order_by(PaperTrade.closed_at.desc()).limit(limit).all()
    
    return {
        "ok": True,
        "count": len(trades),
        "trades": [
            {
                "id": t.id,
                "asset": t.asset,
                "side": t.side,
                "quantity": t.quantity,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "pnl": round(t.pnl, 2),
                "pnl_percent": round(t.pnl_percent, 2),
                "oracle_score_at_entry": t.oracle_score_at_entry,
                "oracle_score_at_exit": t.oracle_score_at_exit,
                "exit_reason": t.exit_reason,
                "opened_at": t.opened_at.isoformat(),
                "closed_at": t.closed_at.isoformat()
            }
            for t in trades
        ]
    }


@router.post("/auto-trade")
async def auto_trade_from_oracle(
    req: AutoTradeRequest,
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Automatically open a position based on ORACLE signal"""
    from app.services.oracle import oracle
    
    # Get ORACLE signal
    try:
        signal = await oracle.generate_signal(req.asset)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get ORACLE signal: {e}")
    
    if not signal:
        raise HTTPException(status_code=400, detail=f"No signal available for {req.asset}")
    
    oracle_score = signal.get("oracle_score", 50)
    signal_type = signal.get("signal_type", "hold")
    
    # Determine trade side based on signal
    if signal_type in ["strong_buy", "buy"]:
        side = "long"
    elif signal_type in ["strong_sell", "sell"]:
        side = "short"
    else:
        return {
            "ok": True,
            "action": "none",
            "message": f"ORACLE signal is {signal_type} (score: {oracle_score}). No trade opened.",
            "signal": signal_type,
            "score": oracle_score
        }
    
    # Open position
    open_req = OpenPositionRequest(
        asset=req.asset,
        asset_type=req.asset_type,
        side=side,
        amount_usd=req.amount_usd,
        stop_loss_percent=signal.get("stop_pct", 5),
        take_profit_percent=signal.get("target_pct", 10)
    )
    
    result = await open_position(open_req, user, db)
    result["oracle_signal"] = signal_type
    result["oracle_score"] = oracle_score
    
    return result


@router.post("/reset")
async def reset_portfolio(
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reset paper trading portfolio to initial state"""
    portfolio = db.query(PaperPortfolio).filter(PaperPortfolio.user_id == user.id).first()
    
    if portfolio:
        # Delete all positions
        db.query(PaperPosition).filter(PaperPosition.portfolio_id == portfolio.id).delete()
        
        # Delete all trades
        db.query(PaperTrade).filter(PaperTrade.portfolio_id == portfolio.id).delete()
        
        # Reset portfolio
        portfolio.cash_balance = portfolio.initial_balance
        portfolio.total_value = portfolio.initial_balance
        portfolio.total_trades = 0
        portfolio.winning_trades = 0
        portfolio.losing_trades = 0
        portfolio.total_pnl = 0
        portfolio.total_pnl_percent = 0
        portfolio.best_trade_pnl = 0
        portfolio.worst_trade_pnl = 0
        
        db.commit()
    
    return {"ok": True, "message": "Portfolio reset to initial balance"}


@router.get("/performance")
async def get_performance_stats(
    user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed performance statistics"""
    portfolio = get_or_create_portfolio(user.id, db)
    trades = db.query(PaperTrade).filter(PaperTrade.user_id == user.id).all()
    
    if not trades:
        return {
            "ok": True,
            "stats": {
                "total_trades": 0,
                "message": "No trades yet. Start paper trading to build your track record."
            }
        }
    
    # Calculate stats
    total_pnl = sum(t.pnl for t in trades)
    winning = [t for t in trades if t.pnl > 0]
    losing = [t for t in trades if t.pnl < 0]
    
    avg_win = sum(t.pnl for t in winning) / len(winning) if winning else 0
    avg_loss = sum(t.pnl for t in losing) / len(losing) if losing else 0
    
    # Calculate by asset
    by_asset = {}
    for t in trades:
        if t.asset not in by_asset:
            by_asset[t.asset] = {"trades": 0, "pnl": 0, "wins": 0}
        by_asset[t.asset]["trades"] += 1
        by_asset[t.asset]["pnl"] += t.pnl
        if t.pnl > 0:
            by_asset[t.asset]["wins"] += 1
    
    # ORACLE accuracy
    oracle_trades = [t for t in trades if t.oracle_signal_at_entry]
    oracle_correct = [t for t in oracle_trades if 
        (t.oracle_signal_at_entry in ["buy", "strong_buy"] and t.pnl > 0) or
        (t.oracle_signal_at_entry in ["sell", "strong_sell"] and t.pnl > 0)]
    oracle_accuracy = (len(oracle_correct) / len(oracle_trades) * 100) if oracle_trades else 0
    
    return {
        "ok": True,
        "stats": {
            "total_trades": len(trades),
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "win_rate": round(len(winning) / len(trades) * 100, 1) if trades else 0,
            "total_pnl": round(total_pnl, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(abs(sum(t.pnl for t in winning) / sum(t.pnl for t in losing)), 2) if losing and sum(t.pnl for t in losing) != 0 else 0,
            "oracle_accuracy": round(oracle_accuracy, 1),
            "oracle_trades": len(oracle_trades),
            "by_asset": [
                {"asset": k, "trades": v["trades"], "pnl": round(v["pnl"], 2), "win_rate": round(v["wins"]/v["trades"]*100, 1)}
                for k, v in sorted(by_asset.items(), key=lambda x: x[1]["pnl"], reverse=True)
            ]
        }
    }
