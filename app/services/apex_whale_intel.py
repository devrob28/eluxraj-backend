"""
APEX Whale Intelligence System
Institutional-grade whale tracking for Crypto AND Stocks
- Crypto: Exchange flows, whale wallets, on-chain analytics
- Stocks: SEC Form 4 insider trading, 13F institutional holdings
"""
import httpx
import asyncio
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Configuration
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY", "")
API_NINJAS_KEY = os.getenv("API_NINJAS_KEY", "")

# Known crypto whale wallets
CRYPTO_WHALES = {
    "0x28c6c06298d514db089934071355e5743bf21d60": {"name": "Binance Hot Wallet", "type": "exchange", "tier": "mega"},
    "0x21a31ee1afc51d94c2efccaa2092ad1028285549": {"name": "Binance Cold", "type": "exchange", "tier": "mega"},
    "0x71660c4005ba85c37ccec55d0c4493e66fe775d3": {"name": "Coinbase Prime", "type": "exchange", "tier": "mega"},
    "0x503828976d22510aad0201ac7ec88293211d23da": {"name": "Coinbase Commerce", "type": "exchange", "tier": "mega"},
    "0x2910543af39aba0cd09dbb2d50200b3e800a63d2": {"name": "Kraken", "type": "exchange", "tier": "large"},
    "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b": {"name": "OKX", "type": "exchange", "tier": "large"},
    "0x9b64203878f24eb0cdf55c8c6fa7d08ba0cf77e5": {"name": "Jump Trading", "type": "market_maker", "tier": "mega"},
    "0x1b3cb81e51011b549d78bf720b0d924ac763a7c2": {"name": "Wintermute", "type": "market_maker", "tier": "mega"},
    "0xe592427a0aece92de3edee1f18e0157c05861564": {"name": "Uniswap V3", "type": "dex", "tier": "mega"},
    "0x5754284f345afc66a98fbb0a0afe71e0f007b949": {"name": "Tether Treasury", "type": "treasury", "tier": "mega"},
}

# Top stocks to track for insider activity
TRACKED_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AMD", "NFLX", "CRM",
    "COIN", "MSTR", "SQ", "PYPL", "V", "MA", "JPM", "GS", "BAC", "PLTR"
]


class ApexWhaleIntelService:
    """Unified whale intelligence for crypto and stocks"""
    
    def __init__(self):
        self.alchemy_url = f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
        self.api_ninjas_key = API_NINJAS_KEY
    
    async def get_unified_whale_feed(self, limit: int = 50) -> Dict:
        """Get combined whale activity from crypto and stocks"""
        crypto_task = self.get_crypto_whale_activity(limit=limit//2)
        stock_task = self.get_stock_insider_activity(limit=limit//2)
        
        crypto_activity, stock_activity = await asyncio.gather(
            crypto_task, stock_task, return_exceptions=True
        )
        
        if isinstance(crypto_activity, Exception):
            logger.error(f"Crypto whale fetch error: {crypto_activity}")
            crypto_activity = []
        if isinstance(stock_activity, Exception):
            logger.error(f"Stock insider fetch error: {stock_activity}")
            stock_activity = []
        
        all_activity = crypto_activity + stock_activity
        all_activity.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        crypto_bullish = sum(1 for a in crypto_activity if a.get("impact") == "bullish")
        crypto_bearish = sum(1 for a in crypto_activity if a.get("impact") == "bearish")
        stock_bullish = sum(1 for a in stock_activity if a.get("impact") == "bullish")
        stock_bearish = sum(1 for a in stock_activity if a.get("impact") == "bearish")
        
        return {
            "ok": True,
            "transactions": all_activity[:limit],
            "summary": {
                "crypto": {
                    "count": len(crypto_activity),
                    "bullish": crypto_bullish,
                    "bearish": crypto_bearish,
                    "sentiment": "bullish" if crypto_bullish > crypto_bearish else "bearish" if crypto_bearish > crypto_bullish else "neutral"
                },
                "stocks": {
                    "count": len(stock_activity),
                    "bullish": stock_bullish,
                    "bearish": stock_bearish,
                    "sentiment": "bullish" if stock_bullish > stock_bearish else "bearish" if stock_bearish > stock_bullish else "neutral"
                },
                "overall_sentiment": self._calc_sentiment(crypto_bullish + stock_bullish, crypto_bearish + stock_bearish)
            },
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def get_crypto_whale_activity(self, limit: int = 25) -> List[Dict]:
        """Get recent crypto whale transactions"""
        all_transfers = []
        priority_wallets = list(CRYPTO_WHALES.keys())[:4]
        
        for wallet in priority_wallets:
            try:
                outflows = await self._get_alchemy_transfers(from_address=wallet, max_count=10)
                for t in outflows:
                    t["direction"] = "outflow"
                    t["whale_info"] = CRYPTO_WHALES.get(wallet.lower(), {"name": "Unknown", "type": "whale", "tier": "large"})
                all_transfers.extend(outflows)
                
                inflows = await self._get_alchemy_transfers(to_address=wallet, max_count=10)
                for t in inflows:
                    t["direction"] = "inflow"
                    t["whale_info"] = CRYPTO_WHALES.get(wallet.lower(), {"name": "Unknown", "type": "whale", "tier": "large"})
                all_transfers.extend(inflows)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error fetching wallet {wallet}: {e}")
        
        formatted = [self._format_crypto_transfer(t) for t in all_transfers]
        formatted.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return formatted[:limit]
    
    async def _get_alchemy_transfers(self, from_address: str = None, to_address: str = None, max_count: int = 20) -> List[Dict]:
        """Fetch transfers from Alchemy API"""
        if not ALCHEMY_API_KEY:
            return []
        
        params = {
            "fromBlock": "0x0",
            "toBlock": "latest",
            "category": ["external", "erc20"],
            "withMetadata": True,
            "maxCount": hex(max_count),
            "order": "desc"
        }
        if from_address:
            params["fromAddress"] = from_address
        if to_address:
            params["toAddress"] = to_address
        
        payload = {"jsonrpc": "2.0", "id": 1, "method": "alchemy_getAssetTransfers", "params": [params]}
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(self.alchemy_url, json=payload)
                data = response.json()
                if "result" in data and "transfers" in data["result"]:
                    return data["result"]["transfers"]
        except Exception as e:
            logger.error(f"Alchemy API error: {e}")
        return []
    
    def _format_crypto_transfer(self, transfer: Dict) -> Dict:
        """Format crypto transfer for unified feed"""
        from_addr = transfer.get("from", "").lower()
        to_addr = transfer.get("to", "").lower()
        from_info = CRYPTO_WHALES.get(from_addr, {"name": self._short_addr(from_addr), "type": "wallet", "tier": "unknown"})
        to_info = CRYPTO_WHALES.get(to_addr, {"name": self._short_addr(to_addr), "type": "wallet", "tier": "unknown"})
        
        direction = transfer.get("direction", "unknown")
        whale_info = transfer.get("whale_info", {})
        
        if whale_info.get("type") == "exchange":
            impact = "bullish" if direction == "outflow" else "bearish"
        else:
            impact = "neutral"
        
        value = transfer.get("value", 0) or 0
        asset = transfer.get("asset", "ETH")
        usd_value = self._estimate_usd(value, asset)
        
        if usd_value >= 10_000_000:
            significance, emoji = "mega", "🐋🐋🐋"
        elif usd_value >= 1_000_000:
            significance, emoji = "large", "🐋🐋"
        elif usd_value >= 100_000:
            significance, emoji = "medium", "🐋"
        else:
            significance, emoji = "small", "🐟"
        
        return {
            "id": transfer.get("hash", ""),
            "timestamp": transfer.get("metadata", {}).get("blockTimestamp", datetime.utcnow().isoformat()),
            "asset_type": "crypto",
            "symbol": asset,
            "amount": value,
            "amount_usd": usd_value,
            "transaction_type": "transfer_out" if direction == "outflow" else "transfer_in",
            "whale_name": whale_info.get("name", "Unknown Whale"),
            "whale_type": whale_info.get("type", "whale"),
            "whale_title": whale_info.get("type", "").replace("_", " ").title(),
            "impact": impact,
            "significance": significance,
            "emoji": emoji,
            "source": "alchemy",
            "from": {"name": from_info["name"], "address": transfer.get("from", "")},
            "to": {"name": to_info["name"], "address": transfer.get("to", "")},
            "tx_hash": transfer.get("hash", ""),
            "blockchain": "ethereum"
        }
    
    async def get_stock_insider_activity(self, limit: int = 25, ticker: str = None) -> List[Dict]:
        """Get stock insider trading from SEC Form 4"""
        if self.api_ninjas_key:
            return await self._fetch_api_ninjas_insider(limit, ticker)
        return await self._fetch_sec_edgar_insider(limit)
    
    async def _fetch_api_ninjas_insider(self, limit: int, ticker: str = None) -> List[Dict]:
        """Fetch from API Ninjas insider trading API"""
        transactions = []
        tickers_to_check = [ticker] if ticker else TRACKED_STOCKS[:10]
        
        async with httpx.AsyncClient(timeout=30) as client:
            for symbol in tickers_to_check:
                try:
                    response = await client.get(
                        f"https://api.api-ninjas.com/v1/insidertrading?ticker={symbol}",
                        headers={"X-Api-Key": self.api_ninjas_key}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        for trade in data[:5]:
                            transactions.append(self._format_insider_trade(trade, symbol))
                    await asyncio.sleep(0.1)
                except Exception as e:
                    logger.error(f"API Ninjas error for {symbol}: {e}")
        
        transactions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return transactions[:limit]
    
    async def _fetch_sec_edgar_insider(self, limit: int) -> List[Dict]:
        """Fallback: Fetch from SEC EDGAR directly (free)"""
        transactions = []
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&company=&dateb=&owner=include&count=40&output=atom",
                    headers={"User-Agent": "ELUXRAJ/1.0 (support@eluxraj.ai)"}
                )
                if response.status_code == 200:
                    import re
                    content = response.text
                    entries = re.findall(r'<entry>(.*?)</entry>', content, re.DOTALL)
                    
                    for entry in entries[:limit]:
                        try:
                            title = re.search(r'<title>(.*?)</title>', entry)
                            updated = re.search(r'<updated>(.*?)</updated>', entry)
                            link = re.search(r'<link href="(.*?)"', entry)
                            
                            if title and "4 -" in title.group(1):
                                title_text = title.group(1)
                                ticker_match = re.search(r'\(([A-Z]{1,5})\)', title_text)
                                ticker = ticker_match.group(1) if ticker_match else "UNK"
                                
                                parts = title_text.split(" - ")
                                insider_name = parts[-1].strip() if len(parts) > 1 else "Unknown"
                                
                                transactions.append({
                                    "id": link.group(1) if link else "",
                                    "timestamp": updated.group(1) if updated else datetime.utcnow().isoformat(),
                                    "asset_type": "stock",
                                    "symbol": ticker,
                                    "amount": 0,
                                    "amount_usd": 0,
                                    "transaction_type": "filing",
                                    "whale_name": insider_name,
                                    "whale_type": "insider",
                                    "whale_title": "Insider",
                                    "impact": "neutral",
                                    "significance": "medium",
                                    "emoji": "👔",
                                    "source": "sec_edgar",
                                    "filing_url": link.group(1) if link else ""
                                })
                        except:
                            continue
        except Exception as e:
            logger.error(f"SEC EDGAR fetch error: {e}")
        return transactions[:limit]
    
    def _format_insider_trade(self, trade: Dict, symbol: str) -> Dict:
        """Format insider trade for unified feed"""
        transaction_type = trade.get("transaction_type", "").lower()
        shares = abs(trade.get("shares", 0) or 0)
        price = trade.get("transaction_price", 0) or 0
        value = shares * price
        
        if "purchase" in transaction_type or "buy" in transaction_type:
            impact, tx_type, emoji = "bullish", "buy", "🟢"
        elif "sale" in transaction_type or "sell" in transaction_type:
            impact, tx_type, emoji = "bearish", "sell", "🔴"
        else:
            impact, tx_type, emoji = "neutral", "other", "⚪"
        
        if value >= 10_000_000:
            significance, size_emoji = "mega", "👔👔👔"
        elif value >= 1_000_000:
            significance, size_emoji = "large", "👔👔"
        elif value >= 100_000:
            significance, size_emoji = "medium", "👔"
        else:
            significance, size_emoji = "small", "👤"
        
        return {
            "id": trade.get("accession_number", ""),
            "timestamp": trade.get("filing_date", datetime.utcnow().strftime("%Y-%m-%d")),
            "asset_type": "stock",
            "symbol": symbol,
            "amount": shares,
            "amount_usd": value,
            "price": price,
            "transaction_type": tx_type,
            "whale_name": trade.get("insider_name", "Unknown Insider"),
            "whale_type": "insider",
            "whale_title": trade.get("insider_position", "Insider"),
            "impact": impact,
            "significance": significance,
            "emoji": f"{emoji} {size_emoji}",
            "source": "sec_form4",
            "company": trade.get("company_name", symbol),
            "filing_url": trade.get("sec_filing_url", "")
        }
    
    async def get_exchange_flows(self) -> Dict:
        """Get exchange inflow/outflow analysis"""
        exchanges = {
            "Binance": {"name": "Binance", "inflow": 0, "outflow": 0},
            "Coinbase": {"name": "Coinbase", "inflow": 0, "outflow": 0},
            "Kraken": {"name": "Kraken", "inflow": 0, "outflow": 0},
        }
        
        transfers = await self.get_crypto_whale_activity(limit=100)
        
        for t in transfers:
            from_name = t.get("from", {}).get("name", "")
            to_name = t.get("to", {}).get("name", "")
            amount = t.get("amount_usd", 0)
            
            for ex_name in exchanges:
                if ex_name in from_name:
                    exchanges[ex_name]["outflow"] += amount
                if ex_name in to_name:
                    exchanges[ex_name]["inflow"] += amount
        
        for name in exchanges:
            exchanges[name]["net_flow"] = exchanges[name]["outflow"] - exchanges[name]["inflow"]
            exchanges[name]["sentiment"] = "bullish" if exchanges[name]["net_flow"] > 0 else "bearish"
        
        total_inflow = sum(e["inflow"] for e in exchanges.values())
        total_outflow = sum(e["outflow"] for e in exchanges.values())
        net_flow = total_outflow - total_inflow
        
        return {
            "ok": True,
            "exchanges": list(exchanges.values()),
            "summary": {
                "total_inflow": total_inflow,
                "total_outflow": total_outflow,
                "net_flow": net_flow,
                "sentiment": "bullish" if net_flow > 0 else "bearish" if net_flow < 0 else "neutral",
                "interpretation": self._interpret_flow(net_flow)
            },
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def _interpret_flow(self, net_flow: float) -> str:
        if net_flow > 10_000_000:
            return "🟢 STRONG ACCUMULATION: Whales withdrawing heavily from exchanges"
        elif net_flow > 1_000_000:
            return "🟢 ACCUMULATION: Net outflows suggest holding behavior"
        elif net_flow < -10_000_000:
            return "🔴 DISTRIBUTION: Large deposits may indicate selling pressure"
        elif net_flow < -1_000_000:
            return "🟡 CAUTION: Increased deposits could signal profit-taking"
        return "⚪ NEUTRAL: Exchange flows balanced"
    
    async def get_whale_insights(self) -> List[Dict]:
        """Generate actionable whale insights"""
        insights = []
        whale_feed = await self.get_unified_whale_feed(limit=50)
        exchange_flows = await self.get_exchange_flows()
        
        net_flow = exchange_flows["summary"]["net_flow"]
        if abs(net_flow) > 500_000:
            direction = "withdrawals" if net_flow > 0 else "deposits"
            insights.append({
                "type": "exchange_flow",
                "title": f"🏦 ${abs(net_flow)/1e6:.1f}M Net Exchange {direction.title()}",
                "description": exchange_flows["summary"]["interpretation"],
                "impact": "bullish" if net_flow > 0 else "bearish",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        for tx in whale_feed.get("transactions", [])[:10]:
            if tx.get("amount_usd", 0) >= 1_000_000:
                insights.append({
                    "type": "whale_move" if tx["asset_type"] == "crypto" else "insider_trade",
                    "title": f"{tx['emoji']} {tx['whale_name']}: ${tx['amount_usd']/1e6:.1f}M {tx['symbol']}",
                    "description": f"{tx['transaction_type'].replace('_', ' ').title()} - {tx.get('whale_title', '')}",
                    "impact": tx.get("impact", "neutral"),
                    "timestamp": tx.get("timestamp", "")
                })
        
        return insights[:10]
    
    async def get_top_insider_buys(self, days: int = 7) -> List[Dict]:
        """Get top insider buys"""
        activity = await self.get_stock_insider_activity(limit=100)
        buys = [t for t in activity if t.get("transaction_type") == "buy"]
        buys.sort(key=lambda x: x.get("amount_usd", 0), reverse=True)
        return buys[:20]
    
    def _short_addr(self, address: str) -> str:
        if not address or len(address) < 10:
            return address or "Unknown"
        return f"{address[:6]}...{address[-4:]}"
    
    def _estimate_usd(self, value: float, asset: str) -> float:
        prices = {"ETH": 3400, "WETH": 3400, "stETH": 3400, "BTC": 94000, "WBTC": 94000, "USDT": 1, "USDC": 1, "DAI": 1, "BUSD": 1, "TUSD": 1, "LINK": 23, "UNI": 14, "AAVE": 340, "MKR": 1500, "CRV": 0.5, "LDO": 2, "RPL": 25, "SNX": 3, "COMP": 90, "SUSHI": 1.5, "YFI": 8000, "BAL": 4, "1INCH": 0.5}
        return value * prices.get(asset, 0) if value else 0
    
    def _calc_sentiment(self, bullish: int, bearish: int) -> str:
        total = bullish + bearish
        if total == 0:
            return "neutral"
        ratio = bullish / total
        if ratio >= 0.6:
            return "bullish"
        elif ratio <= 0.4:
            return "bearish"
        return "neutral"


# Singleton
apex_whale_intel = ApexWhaleIntelService()
