"""
Weekly AI Brief Service
Auto-generates weekly market analysis for retention
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import Session
from app.db.base import Base
from app.services.market_bias import market_bias_service
from app.core.logging import logger


class WeeklyBrief(Base):
    """Stored weekly AI briefs"""
    __tablename__ = "weekly_briefs"
    
    id = Column(Integer, primary_key=True, index=True)
    week_start = Column(DateTime, nullable=False, index=True)
    week_end = Column(DateTime, nullable=False)
    
    # Content
    title = Column(String(200), nullable=False)
    summary = Column(Text, nullable=False)
    market_overview = Column(Text)
    top_performers = Column(JSON, default=list)
    worst_performers = Column(JSON, default=list)
    key_events = Column(JSON, default=list)
    outlook = Column(Text)
    
    # Scenarios
    bull_case = Column(Text)
    bear_case = Column(Text)
    base_case = Column(Text)
    
    # Metadata
    tier_access = Column(String(20), default="pro")  # lite, pro, elite
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class WeeklyBriefService:
    """Generate and manage weekly briefs"""
    
    async def generate_weekly_brief(self, db: Session) -> WeeklyBrief:
        """Generate a new weekly brief"""
        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=now.weekday(), hours=now.hour, minutes=now.minute)
        week_end = week_start + timedelta(days=6, hours=23, minutes=59)
        
        # Get market data for major assets
        symbols = ["BTC", "ETH", "SOL", "XRP", "DOGE", "ADA"]
        assets_data = []
        
        for symbol in symbols:
            data = await market_bias_service.get_market_data(symbol)
            if data:
                assets_data.append({
                    "symbol": symbol,
                    "price": data.get("price"),
                    "change_24h": data.get("change_24h", 0),
                    "change_7d": data.get("change_7d", 0)
                })
        
        # Sort by 7d performance
        assets_data.sort(key=lambda x: x.get("change_7d", 0), reverse=True)
        
        top_performers = assets_data[:3]
        worst_performers = list(reversed(assets_data[-3:]))
        
        # Calculate overall market sentiment
        avg_change = sum(a.get("change_7d", 0) for a in assets_data) / len(assets_data) if assets_data else 0
        
        if avg_change > 5:
            sentiment = "bullish"
            outlook_text = "Markets are showing strong bullish momentum. Consider maintaining long positions but watch for overextension signals."
        elif avg_change < -5:
            sentiment = "bearish"
            outlook_text = "Markets are under pressure. Consider reducing exposure and waiting for stabilization signals before adding positions."
        else:
            sentiment = "neutral"
            outlook_text = "Markets are consolidating in a range. Look for breakout opportunities but maintain tight risk management."
        
        # Generate brief content
        title = f"Weekly AI Brief: {week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}"
        
        summary = f"This week, the crypto market showed {sentiment} sentiment with an average 7-day change of {avg_change:.1f}%. "
        if top_performers:
            summary += f"{top_performers[0]['symbol']} led gains at {top_performers[0].get('change_7d', 0):.1f}%. "
        if worst_performers and worst_performers[0].get('change_7d', 0) < 0:
            summary += f"{worst_performers[0]['symbol']} saw the largest decline at {worst_performers[0].get('change_7d', 0):.1f}%."
        
        market_overview = f"""
The overall crypto market cap {"increased" if avg_change > 0 else "decreased"} this week.

Key observations:
- Bitcoin {"maintained" if abs(assets_data[0].get('change_7d', 0) if assets_data else 0) < 3 else "showed significant movement in"} its position as market leader
- Altcoins {"outperformed" if any(a.get('change_7d', 0) > assets_data[0].get('change_7d', 0) for a in assets_data[1:]) else "followed"} BTC's lead
- Trading volumes {"remained elevated" if sentiment == "bullish" else "showed typical patterns"}
""".strip()
        
        # Scenarios
        btc_price = assets_data[0].get("price", 100000) if assets_data else 100000
        
        bull_case = f"If momentum continues, BTC could test ${int(btc_price * 1.15):,} (+15%). Key catalysts: institutional inflows, positive regulatory news, ETF momentum."
        bear_case = f"Downside risk targets ${int(btc_price * 0.85):,} (-15%) if macro conditions deteriorate. Watch for: rate hike concerns, regulatory crackdowns, whale distribution."
        base_case = f"Most likely scenario: Range-bound trading between ${int(btc_price * 0.95):,} and ${int(btc_price * 1.05):,} as market digests recent moves."
        
        # Create brief
        brief = WeeklyBrief(
            week_start=week_start,
            week_end=week_end,
            title=title,
            summary=summary,
            market_overview=market_overview,
            top_performers=[{"symbol": a["symbol"], "change": a.get("change_7d", 0)} for a in top_performers],
            worst_performers=[{"symbol": a["symbol"], "change": a.get("change_7d", 0)} for a in worst_performers],
            key_events=[
                "Market sentiment shifted " + sentiment,
                f"Average 7-day change: {avg_change:.1f}%",
                f"Top performer: {top_performers[0]['symbol'] if top_performers else 'N/A'}"
            ],
            outlook=outlook_text,
            bull_case=bull_case,
            bear_case=bear_case,
            base_case=base_case,
            tier_access="pro"
        )
        
        db.add(brief)
        db.commit()
        db.refresh(brief)
        
        logger.info(f"Generated weekly brief: {title}")
        return brief
    
    def get_latest_brief(self, db: Session, user_tier: str = "lite") -> Optional[Dict]:
        """Get the latest weekly brief accessible to user tier"""
        tier_priority = {"lite": 0, "pro": 1, "elite": 2}
        user_priority = tier_priority.get(user_tier, 0)
        
        brief = db.query(WeeklyBrief).order_by(WeeklyBrief.created_at.desc()).first()
        
        if not brief:
            return None
        
        brief_priority = tier_priority.get(brief.tier_access, 1)
        
        # Check access
        if user_priority < brief_priority:
            return {
                "locked": True,
                "title": brief.title,
                "summary": brief.summary[:100] + "...",
                "required_tier": brief.tier_access,
                "message": f"Upgrade to {brief.tier_access.upper()} to access the full weekly brief"
            }
        
        return {
            "locked": False,
            "id": brief.id,
            "title": brief.title,
            "week_start": brief.week_start.isoformat(),
            "week_end": brief.week_end.isoformat(),
            "summary": brief.summary,
            "market_overview": brief.market_overview,
            "top_performers": brief.top_performers,
            "worst_performers": brief.worst_performers,
            "key_events": brief.key_events,
            "outlook": brief.outlook,
            "bull_case": brief.bull_case,
            "bear_case": brief.bear_case,
            "base_case": brief.base_case,
            "created_at": brief.created_at.isoformat()
        }
    
    def get_all_briefs(self, db: Session, limit: int = 10) -> List[Dict]:
        """Get list of all briefs (for archive)"""
        briefs = db.query(WeeklyBrief).order_by(WeeklyBrief.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": b.id,
                "title": b.title,
                "week_start": b.week_start.isoformat(),
                "summary": b.summary[:150] + "..." if len(b.summary) > 150 else b.summary,
                "created_at": b.created_at.isoformat()
            }
            for b in briefs
        ]


weekly_brief_service = WeeklyBriefService()
