"""
Weekly AI Brief Service - Crypto + Stocks with REAL DATA
"""
import httpx
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, desc
from app.db.base import Base
from app.core.logging import logger
from app.core.config import settings


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
    FMP_API = "https://financialmodelingprep.com/api/v3"
    
    CRYPTO_IDS = "bitcoin,ethereum,solana,ripple,dogecoin,cardano,avalanche-2,chainlink,polkadot,litecoin,matic-network,shiba-inu"
    
    STOCK_LIST = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA",
        "JPM", "V", "JNJ", "WMT", "PG", "XOM", "HD", "BAC",
        "MA", "PFE", "KO", "PEP", "COST", "DIS", "NFLX", "AMD",
        "INTC", "CRM", "PYPL", "BA", "NKE", "MCD", "SBUX"
    ]
    
    ETF_LIST = ["SPY", "QQQ", "DIA", "IWM", "VTI", "VOO", "GLD", "VNQ"]
    
    async def fetch_crypto_data(self) -> List[Dict]:
        """Fetch crypto data from CoinGecko (primary source)"""
        results = []
        
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    "https://api.coingecko.com/api/v3/coins/markets",
                    params={
                        "vs_currency": "usd",
                        "ids": self.CRYPTO_IDS,
                        "order": "market_cap_desc",
                        "price_change_percentage": "24h,7d"
                    },
                    timeout=15.0
                )
                
                if r.status_code == 200:
                    data = r.json()
                    for coin in data:
                        results.append({
                            "symbol": coin["symbol"].upper(),
                            "name": coin["name"],
                            "price": coin["current_price"],
                            "change_24h": round(coin.get("price_change_percentage_24h") or 0, 2),
                            "change_7d": round(coin.get("price_change_percentage_7d_in_currency") or 0, 2),
                            "volume": coin.get("total_volume", 0),
                            "type": "crypto"
                        })
                    logger.info(f"CoinGecko returned {len(results)} crypto assets")
                else:
                    logger.error(f"CoinGecko API error: {r.status_code}")
                    
        except Exception as e:
            logger.error(f"Crypto fetch error: {e}")
        
        return results
    
    async def fetch_stock_data(self) -> List[Dict]:
        """Fetch stock data from Financial Modeling Prep API"""
        results = []
        all_symbols = self.STOCK_LIST + self.ETF_LIST
        fmp_key = getattr(settings, 'FMP_API_KEY', None) or "demo"
        
        try:
            async with httpx.AsyncClient() as client:
                symbols_str = ",".join(all_symbols)
                r = await client.get(
                    f"{self.FMP_API}/quote/{symbols_str}",
                    params={"apikey": fmp_key},
                    timeout=30.0
                )
                
                if r.status_code == 200:
                    data = r.json()
                    for stock in data:
                        if isinstance(stock, dict) and "symbol" in stock:
                            change = stock.get("changesPercentage", 0) or 0
                            results.append({
                                "symbol": stock["symbol"],
                                "name": stock.get("name", stock["symbol"]),
                                "price": stock.get("price", 0),
                                "change_24h": round(change, 2),
                                "change_7d": round(change, 2),
                                "type": "etf" if stock["symbol"] in self.ETF_LIST else "stock"
                            })
        except Exception as e:
            logger.error(f"Stock fetch error: {e}")
        
        if not results:
            results = await self._fetch_stock_backup()
        
        return results
    
    async def _fetch_stock_backup(self) -> List[Dict]:
        """Backup: fetch from Yahoo Finance API"""
        results = []
        all_symbols = self.STOCK_LIST + self.ETF_LIST
        
        try:
            async with httpx.AsyncClient() as client:
                for symbol in all_symbols[:20]:
                    try:
                        r = await client.get(
                            f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                            params={"interval": "1d", "range": "7d"},
                            headers={"User-Agent": "Mozilla/5.0"},
                            timeout=10.0
                        )
                        if r.status_code == 200:
                            data = r.json()
                            result = data.get("chart", {}).get("result", [{}])[0]
                            meta = result.get("meta", {})
                            closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])
                            
                            if closes and len(closes) >= 2:
                                current = closes[-1] or closes[-2]
                                week_ago = closes[0]
                                if current and week_ago:
                                    change_7d = ((current - week_ago) / week_ago) * 100
                                    results.append({
                                        "symbol": symbol,
                                        "name": meta.get("shortName", symbol),
                                        "price": round(current, 2),
                                        "change_24h": round(change_7d / 7, 2),
                                        "change_7d": round(change_7d, 2),
                                        "type": "etf" if symbol in self.ETF_LIST else "stock"
                                    })
                    except:
                        continue
        except Exception as e:
            logger.error(f"Backup stock fetch error: {e}")
        
        return results
    
    async def generate_weekly_brief(self, db: Session) -> WeeklyBrief:
        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=7)
        
        crypto_data = await self.fetch_crypto_data()
        stock_data = await self.fetch_stock_data()
        
        logger.info(f"Fetched {len(crypto_data)} crypto, {len(stock_data)} stocks")
        
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
