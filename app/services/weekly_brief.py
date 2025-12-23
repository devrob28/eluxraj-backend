"""
Weekly AI Brief Service
Generates comprehensive weekly market analysis for crypto AND stocks
"""
import httpx
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, desc
from app.db.base import Base
from app.core.logging import logger


class WeeklyBrief(Base):
    __tablename__ = "weekly_briefs"
    
    id = Column(Integer, primary_key=True, index=True)
    week_start = Column(DateTime, nullable=False)
    week_end = Column(DateTime, nullable=False)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=False)
    market_overview = Column(Text)
    crypto_top_performers = Column(JSON)
    crypto_worst_performers = Column(JSON)
    stock_top_performers = Column(JSON)
    stock_worst_performers = Column(JSON)
    key_events = Column(JSON)
    bull_case = Column(Text)
    bear_case = Column(Text)
    base_case = Column(Text)
    tier_required = Column(String(20), default="pro")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class WeeklyBriefService:
    COINGECKO_API = "https://api.coingecko.com/api/v3"
    
    CRYPTO_LIST = {
        "bitcoin": "BTC", "ethereum": "ETH", "solana": "SOL",
        "ripple": "XRP", "dogecoin": "DOGE", "cardano": "ADA",
        "avalanche-2": "AVAX", "chainlink": "LINK", "polkadot": "DOT",
        "litecoin": "LTC"
    }
    
    STOCK_LIST = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AMD", "INTC", "CRM",
        "JPM", "BAC", "WFC", "GS", "MS", "V", "MA", "AXP", "BLK", "C",
        "JNJ", "UNH", "PFE", "ABBV", "MRK", "TMO", "ABT", "DHR", "BMY", "LLY",
        "WMT", "PG", "KO", "PEP", "COST", "MCD", "NKE", "SBUX", "HD", "LOW",
        "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "HAL",
        "CAT", "BA", "HON", "UPS", "GE", "MMM", "LMT", "RTX", "DE", "UNP",
        "SPY", "QQQ", "DIA", "IWM", "VTI", "VOO", "VEA", "VWO", "BND", "GLD",
        "NFLX", "DIS", "PYPL", "SQ", "SHOP", "UBER", "ABNB", "COIN", "PLTR", "SNOW"
    ]
    
    FUND_LIST = [
        "SPY", "VOO", "VTI", "QQQ", "IVV", "VEA", "VWO", "BND", "AGG", "VNQ",
        "VXUS", "VIG", "VYM", "SCHD", "VGT", "XLF", "XLE", "XLK", "XLV", "XLI"
    ]
    
    async def fetch_crypto_data(self) -> List[Dict]:
        try:
            ids = ",".join(self.CRYPTO_LIST.keys())
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    f"{self.COINGECKO_API}/coins/markets",
                    params={
                        "vs_currency": "usd",
                        "ids": ids,
                        "price_change_percentage": "7d",
                        "order": "market_cap_desc"
                    },
                    timeout=15.0
                )
                if r.status_code == 200:
                    data = r.json()
                    return [
                        {
                            "symbol": self.CRYPTO_LIST.get(coin["id"], coin["symbol"].upper()),
                            "name": coin["name"],
                            "price": coin["current_price"],
                            "change_7d": coin.get("price_change_percentage_7d_in_currency", 0) or 0,
                            "market_cap": coin.get("market_cap", 0),
                            "type": "crypto"
                        }
                        for coin in data
                    ]
        except Exception as e:
            logger.error(f"Crypto fetch error: {e}")
        return []
    
    async def fetch_stock_data(self) -> List[Dict]:
        import yfinance as yf
        from concurrent.futures import ThreadPoolExecutor
        
        results = []
        all_symbols = list(set(self.STOCK_LIST + self.FUND_LIST))
        
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=10)
            
            def fetch_single(symbol):
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(start=start_date, end=end_date)
                    if len(hist) >= 2:
                        current_price = hist['Close'].iloc[-1]
                        week_ago_price = hist['Close'].iloc[0]
                        change_7d = ((current_price - week_ago_price) / week_ago_price) * 100
                        
                        info = ticker.info
                        return {
                            "symbol": symbol,
                            "name": info.get("shortName", symbol),
                            "price": round(current_price, 2),
                            "change_7d": round(change_7d, 2),
                            "market_cap": info.get("marketCap", 0),
                            "type": "etf" if symbol in self.FUND_LIST else "stock"
                        }
                except Exception as e:
                    logger.warning(f"Failed to fetch {symbol}: {e}")
                return None
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = list(executor.map(fetch_single, all_symbols))
                results = [r for r in futures if r is not None]
                
        except Exception as e:
            logger.error(f"Stock fetch error: {e}")
        
        return results
    
    async def generate_weekly_brief(self, db: Session) -> WeeklyBrief:
        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=7)
        
        crypto_data = await self.fetch_crypto_data()
        stock_data = await self.fetch_stock_data()
        
        crypto_sorted = sorted(crypto_data, key=lambda x: x["change_7d"], reverse=True)
        stock_sorted = sorted(stock_data, key=lambda x: x["change_7d"], reverse=True)
        
        crypto_top = crypto_sorted[:3] if crypto_sorted else []
        crypto_worst = crypto_sorted[-3:] if len(crypto_sorted) >= 3 else crypto_sorted
        
        stock_top = stock_sorted[:5] if stock_sorted else []
        stock_worst = stock_sorted[-5:] if len(stock_sorted) >= 5 else stock_sorted
        
        crypto_avg = sum(c["change_7d"] for c in crypto_data) / len(crypto_data) if crypto_data else 0
        stock_avg = sum(s["change_7d"] for s in stock_data) / len(stock_data) if stock_data else 0
        
        overall_sentiment = "bullish" if (crypto_avg + stock_avg) / 2 > 2 else "bearish" if (crypto_avg + stock_avg) / 2 < -2 else "neutral"
        
        summary = self._generate_summary(crypto_data, stock_data, crypto_avg, stock_avg, overall_sentiment)
        market_overview = self._generate_market_overview(crypto_avg, stock_avg, crypto_top, stock_top)
        key_events = self._generate_key_events(crypto_data, stock_data, crypto_avg, stock_avg)
        bull_case, bear_case, base_case = self._generate_scenarios(crypto_top, stock_top, crypto_avg, stock_avg)
        
        brief = WeeklyBrief(
            week_start=week_start,
            week_end=now,
            title=f"Weekly AI Brief: {week_start.strftime('%b %d')} - {now.strftime('%b %d, %Y')}",
            summary=summary,
            market_overview=market_overview,
            crypto_top_performers=crypto_top,
            crypto_worst_performers=crypto_worst,
            stock_top_performers=stock_top,
            stock_worst_performers=stock_worst,
            key_events=key_events,
            bull_case=bull_case,
            bear_case=bear_case,
            base_case=base_case,
            tier_required="pro"
        )
        
        db.add(brief)
        db.commit()
        db.refresh(brief)
        
        logger.info(f"Generated weekly brief: {brief.title}")
        return brief
    
    def _generate_summary(self, crypto_data, stock_data, crypto_avg, stock_avg, sentiment):
        crypto_leader = max(crypto_data, key=lambda x: x["change_7d"]) if crypto_data else None
        stock_leader = max(stock_data, key=lambda x: x["change_7d"]) if stock_data else None
        crypto_laggard = min(crypto_data, key=lambda x: x["change_7d"]) if crypto_data else None
        
        parts = [f"This week, markets showed {sentiment} sentiment."]
        
        if crypto_data:
            parts.append(f"Crypto averaged {crypto_avg:.1f}% with {crypto_leader['symbol']} leading at {crypto_leader['change_7d']:+.1f}%.")
        
        if stock_data:
            parts.append(f"Stocks averaged {stock_avg:.1f}% with {stock_leader['symbol']} top performer at {stock_leader['change_7d']:+.1f}%.")
        
        if crypto_laggard:
            parts.append(f"{crypto_laggard['symbol']} saw the largest crypto decline at {crypto_laggard['change_7d']:.1f}%.")
            
        return " ".join(parts)
    
    def _generate_market_overview(self, crypto_avg, stock_avg, crypto_top, stock_top):
        lines = []
        
        if crypto_avg > 0:
            lines.append("The crypto market showed strength this week.")
        else:
            lines.append("The crypto market faced headwinds this week.")
            
        if stock_avg > 0:
            lines.append("Traditional equities posted gains.")
        else:
            lines.append("Traditional equities pulled back.")
        
        lines.append("\nKey observations:")
        lines.append("- Bitcoin continues to influence overall crypto sentiment")
        lines.append("- Tech stocks remain a key driver of equity performance")
        lines.append("- Trading volumes showed typical weekly patterns")
        
        return "\n".join(lines)
    
    def _generate_key_events(self, crypto_data, stock_data, crypto_avg, stock_avg):
        events = []
        
        overall = (crypto_avg + stock_avg) / 2
        if overall > 3:
            events.append("Market sentiment shifted bullish")
        elif overall < -3:
            events.append("Market sentiment shifted bearish")
        else:
            events.append("Markets traded in a consolidation range")
        
        events.append(f"Crypto 7-day average: {crypto_avg:+.1f}%")
        events.append(f"Stock 7-day average: {stock_avg:+.1f}%")
        
        if crypto_data:
            top_crypto = max(crypto_data, key=lambda x: x["change_7d"])
            events.append(f"Top crypto performer: {top_crypto['symbol']}")
            
        if stock_data:
            top_stock = max(stock_data, key=lambda x: x["change_7d"])
            events.append(f"Top stock performer: {top_stock['symbol']}")
        
        return events
    
    def _generate_scenarios(self, crypto_top, stock_top, crypto_avg, stock_avg):
        bull = "If momentum continues, we could see:\n"
        if crypto_top:
            bull += f"- {crypto_top[0]['symbol']} potentially reaching ${crypto_top[0]['price'] * 1.15:,.0f}\n"
        if stock_top:
            bull += f"- {stock_top[0]['symbol']} testing ${stock_top[0]['price'] * 1.10:.2f}\n"
        bull += "- Increased institutional inflows\n- Positive sentiment driving FOMO buying"
        
        bear = "Downside risks include:\n"
        if crypto_top:
            bear += f"- {crypto_top[0]['symbol']} retracing to ${crypto_top[0]['price'] * 0.85:,.0f}\n"
        if stock_top:
            bear += f"- {stock_top[0]['symbol']} pulling back to ${stock_top[0]['price'] * 0.90:.2f}\n"
        bear += "- Macro headwinds from rate decisions\n- Risk-off sentiment in global markets"
        
        base = "Most likely scenario:\n"
        if crypto_top:
            base += f"- {crypto_top[0]['symbol']} consolidating around ${crypto_top[0]['price'] * 1.02:,.0f}\n"
        if stock_top:
            base += f"- {stock_top[0]['symbol']} ranging near ${stock_top[0]['price'] * 1.02:.2f}\n"
        base += "- Continued sector rotation\n- Normal volatility patterns"
        
        return bull, bear, base
    
    def get_latest_brief(self, db: Session, user_tier: str = "free") -> Optional[Dict]:
        brief = db.query(WeeklyBrief).order_by(desc(WeeklyBrief.created_at)).first()
        
        if not brief:
            return None
        
        tier_access = {"free": 0, "lite": 1, "pro": 2, "elite": 3, "admin": 4}
        required_access = tier_access.get(brief.tier_required, 2)
        user_access = tier_access.get(user_tier, 0)
        
        if user_access < required_access:
            return {
                "id": brief.id,
                "title": brief.title,
                "summary": brief.summary[:200] + "...",
                "locked": True,
                "tier_required": brief.tier_required
            }
        
        return {
            "id": brief.id,
            "title": brief.title,
            "week_start": brief.week_start.isoformat(),
            "week_end": brief.week_end.isoformat(),
            "summary": brief.summary,
            "market_overview": brief.market_overview,
            "crypto_top_performers": brief.crypto_top_performers,
            "crypto_worst_performers": brief.crypto_worst_performers,
            "stock_top_performers": brief.stock_top_performers,
            "stock_worst_performers": brief.stock_worst_performers,
            "key_events": brief.key_events,
            "bull_case": brief.bull_case,
            "bear_case": brief.bear_case,
            "base_case": brief.base_case,
            "locked": False,
            "created_at": brief.created_at.isoformat()
        }
    
    def get_all_briefs(self, db: Session, limit: int = 10) -> List[Dict]:
        briefs = db.query(WeeklyBrief).order_by(desc(WeeklyBrief.created_at)).limit(limit).all()
        return [
            {
                "id": b.id,
                "title": b.title,
                "week_start": b.week_start.isoformat(),
                "week_end": b.week_end.isoformat(),
                "summary": b.summary[:150] + "...",
                "created_at": b.created_at.isoformat()
            }
            for b in briefs
        ]


weekly_brief_service = WeeklyBriefService()
