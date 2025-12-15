"""
Watchlist API - Track favorite assets
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime, timezone
from typing import List
from pydantic import BaseModel
from app.db.session import get_db
from app.db.base import Base
from app.core.deps import get_current_user

router = APIRouter()

class WatchlistItem(Base):
    __tablename__ = "watchlist_items"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    asset = Column(String, nullable=False)
    asset_type = Column(String, default="crypto")
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class WatchlistAdd(BaseModel):
    asset: str
    asset_type: str = "crypto"

@router.get("")
async def get_watchlist(user=Depends(get_current_user), db: Session=Depends(get_db)):
    items = db.query(WatchlistItem).filter(WatchlistItem.user_id == user.id).all()
    return {"ok": True, "count": len(items), "items": [{"id": i.id, "asset": i.asset, "asset_type": i.asset_type, "added_at": i.added_at.isoformat()} for i in items]}

@router.post("")
async def add_to_watchlist(item: WatchlistAdd, user=Depends(get_current_user), db: Session=Depends(get_db)):
    existing = db.query(WatchlistItem).filter(WatchlistItem.user_id == user.id, WatchlistItem.asset == item.asset.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already in watchlist")
    db_item = WatchlistItem(user_id=user.id, asset=item.asset.upper(), asset_type=item.asset_type)
    db.add(db_item)
    db.commit()
    return {"ok": True, "message": f"{item.asset.upper()} added to watchlist"}

@router.delete("/{asset}")
async def remove_from_watchlist(asset: str, user=Depends(get_current_user), db: Session=Depends(get_db)):
    item = db.query(WatchlistItem).filter(WatchlistItem.user_id == user.id, WatchlistItem.asset == asset.upper()).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not in watchlist")
    db.delete(item)
    db.commit()
    return {"ok": True, "message": f"{asset.upper()} removed from watchlist"}
