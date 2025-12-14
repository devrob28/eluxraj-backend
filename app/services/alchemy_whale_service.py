"""
Alchemy Whale Tracking Service
Real-time whale tracking using Alchemy webhooks and APIs
"""
import os
import httpx
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY", "")
ALCHEMY_BASE_URL = f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"

WHALE_WALLETS = {
    "0x28C6c06298d514Db089934071355E5743bf21d60": {"name": "Binance", "type": "exchange"},
    "0x21a31Ee1afC51d94C2eFcCAa2092aD1028285549": {"name": "Binance", "type": "exchange"},
    "0x71660c4005BA85c37ccec55d0C4493E66Fe775d3": {"name": "Coinbase", "type": "exchange"},
    "0x503828976D22510aad0201ac7EC88293211D23Da": {"name": "Coinbase", "type": "exchange"},
    "0x2910543Af39abA0Cd09dBb2D50200b3E800A63D2": {"name": "Kraken", "type": "exchange"},
    "0x6cC5F688a315f3dC28A7781717a9A798a59fDA7b": {"name": "OKX", "type": "exchange"},
    "0x236F9F97e0E62388479bf9E5BA4889e46B0273C3": {"name": "Bitfinex", "type": "exchange"},
    "0x9B64203878F24eB0CDF55c8c6fA7D08Ba0cF77E5": {"name": "Jump Trading", "type": "whale"},
    "0x1B3cB81E51011b549d78bf720b0d924ac763A7C2": {"name": "Wintermute", "type": "whale"},
    "0xE592427A0AEce92De3Edee1F18E0157C05861564": {"name": "Uniswap V3", "type": "dex"},
    "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D": {"name": "Uniswap V2", "type": "dex"},
    "0x5754284f345afc66a98fbB0a0Afe71e0F007B949": {"name": "Tether Treasury", "type": "treasury"},
}


class AlchemyWhaleService:
    def __init__(self):
        self.api_key = ALCHEMY_API_KEY
        self.base_url = f"https://eth-mainnet.g.alchemy.com/v2/{self.api_key}"
        self.whale_wallets = WHALE_WALLETS
    
    async def get_asset_transfers(self, from_address: Optional[str] = None, to_address: Optional[str] = None, max_count: int = 50) -> List[Dict]:
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
                response = await client.post(self.base_url, json=payload)
                data = response.json()
                if "result" in data and "transfers" in data["result"]:
                    return data["result"]["transfers"]
                return []
        except Exception as e:
            logger.error(f"Alchemy API error: {e}")
            return []
    
    async def get_whale_transfers(self, limit: int = 20) -> List[Dict]:
        all_transfers = []
        priority_wallets = [
            "0x28C6c06298d514Db089934071355E5743bf21d60",
            "0x71660c4005BA85c37ccec55d0C4493E66Fe775d3",
            "0x2910543Af39abA0Cd09dBb2D50200b3E800A63D2",
        ]
        
        for wallet in priority_wallets:
            transfers = await self.get_asset_transfers(from_address=wallet, max_count=10)
            for t in transfers:
                t["direction"] = "outflow"
                t["whale_info"] = self.whale_wallets.get(wallet, {"name": "Unknown", "type": "whale"})
            all_transfers.extend(transfers)
            await asyncio.sleep(0.2)
            
            transfers = await self.get_asset_transfers(to_address=wallet, max_count=10)
            for t in transfers:
                t["direction"] = "inflow"
                t["whale_info"] = self.whale_wallets.get(wallet, {"name": "Unknown", "type": "whale"})
            all_transfers.extend(transfers)
            await asyncio.sleep(0.2)
        
        all_transfers.sort(key=lambda x: int(x.get("blockNum", "0x0"), 16), reverse=True)
        return [self._format_transfer(t) for t in all_transfers[:limit]]
    
    def _format_transfer(self, transfer: Dict) -> Dict:
        from_addr = transfer.get("from", "")
        to_addr = transfer.get("to", "")
        from_info = self.whale_wallets.get(from_addr, {"name": self._short_addr(from_addr), "type": "wallet"})
        to_info = self.whale_wallets.get(to_addr, {"name": self._short_addr(to_addr), "type": "wallet"})
        
        direction = transfer.get("direction", "unknown")
        impact = "bullish" if direction == "outflow" else "bearish" if direction == "inflow" else "neutral"
        
        value = transfer.get("value", 0) or 0
        asset = transfer.get("asset", "ETH")
        usd_value = self._estimate_usd_value(value, asset)
        
        return {
            "id": transfer.get("hash", ""),
            "timestamp": transfer.get("metadata", {}).get("blockTimestamp", datetime.utcnow().isoformat()),
            "blockchain": "ethereum",
            "symbol": asset,
            "amount": value,
            "amount_usd": usd_value,
            "from": {"name": from_info["name"], "type": from_info["type"], "address": from_addr},
            "to": {"name": to_info["name"], "type": to_info["type"], "address": to_addr},
            "impact": impact,
            "source": "alchemy",
            "tx_hash": transfer.get("hash", "")
        }
    
    def _short_addr(self, address: str) -> str:
        if not address or len(address) < 10:
            return address or "Unknown"
        return f"{address[:6]}...{address[-4:]}"
    
    def _estimate_usd_value(self, value: float, asset: str) -> float:
        prices = {"ETH": 3500, "WETH": 3500, "USDT": 1, "USDC": 1, "DAI": 1, "WBTC": 100000}
        return value * prices.get(asset, 1) if value else 0
    
    async def get_exchange_flows(self) -> Dict:
        exchanges = {"Binance": {"name": "Binance", "type": "CEX", "inflow": 0, "outflow": 0, "net_flow": 0},
                     "Coinbase": {"name": "Coinbase", "type": "CEX", "inflow": 0, "outflow": 0, "net_flow": 0},
                     "Kraken": {"name": "Kraken", "type": "CEX", "inflow": 0, "outflow": 0, "net_flow": 0}}
        
        transfers = await self.get_whale_transfers(limit=50)
        for t in transfers:
            if t["from"]["type"] == "exchange" and t["from"]["name"] in exchanges:
                exchanges[t["from"]["name"]]["outflow"] += t["amount_usd"]
            if t["to"]["type"] == "exchange" and t["to"]["name"] in exchanges:
                exchanges[t["to"]["name"]]["inflow"] += t["amount_usd"]
        
        for name in exchanges:
            exchanges[name]["net_flow"] = exchanges[name]["outflow"] - exchanges[name]["inflow"]
        
        return {"exchanges": list(exchanges.values()), "total_inflow": sum(e["inflow"] for e in exchanges.values()),
                "total_outflow": sum(e["outflow"] for e in exchanges.values())}
    
    async def get_insights(self) -> List[Dict]:
        insights = []
        flows = await self.get_exchange_flows()
        net_flow = flows["total_outflow"] - flows["total_inflow"]
        
        if abs(net_flow) > 100000:
            direction = "Outflows" if net_flow > 0 else "Inflows"
            sentiment = "bullish" if net_flow > 0 else "bearish"
            insights.append({"title": f"🐋 {'Strong Accumulation' if net_flow > 0 else 'Selling Pressure'}: ${abs(net_flow)/1e6:.1f}M Net Exchange {direction}",
                           "tags": [sentiment, "whale", "exchange"], "time": "Live", "updates": len(flows["exchanges"]), "source": "alchemy"})
        
        for ex in flows["exchanges"]:
            if ex["outflow"] > 1000000:
                insights.append({"title": f"🏦 {ex['name']} Whales Withdraw ${ex['outflow']/1e6:.1f}M",
                               "tags": ["bullish", "exchange"], "time": "Live", "updates": 1, "source": "alchemy"})
            elif ex["inflow"] > 1000000:
                insights.append({"title": f"⚠️ ${ex['inflow']/1e6:.1f}M Deposited to {ex['name']}",
                               "tags": ["bearish", "exchange"], "time": "Live", "updates": 1, "source": "alchemy"})
        return insights[:8]
    
    async def get_sentiment(self) -> Dict:
        transfers = await self.get_whale_transfers(limit=30)
        bullish = sum(1 for t in transfers if t["impact"] == "bullish")
        bearish = sum(1 for t in transfers if t["impact"] == "bearish")
        total = bullish + bearish
        score = int((bullish / total) * 100) if total > 0 else 50
        
        if score >= 60:
            sentiment, emoji = "Bullish", "🟢"
        elif score <= 40:
            sentiment, emoji = "Bearish", "🔴"
        else:
            sentiment, emoji = "Neutral", "🟡"
        
        flows = await self.get_exchange_flows()
        return {"ok": True, "sentiment": sentiment, "sentiment_emoji": emoji, "sentiment_score": score,
                "bullish_signals": bullish, "bearish_signals": bearish,
                "net_flow_usd": flows["total_outflow"] - flows["total_inflow"], "source": "alchemy"}


alchemy_whale_service = AlchemyWhaleService()
