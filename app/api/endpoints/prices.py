from fastapi import APIRouter
import httpx

router = APIRouter()

@router.get("/crypto")
async def get_crypto_prices():
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    results = []
    async with httpx.AsyncClient() as client:
        for symbol in symbols:
            resp = await client.get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}")
            results.append(resp.json())
    return results
