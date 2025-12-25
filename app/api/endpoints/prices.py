from fastapi import APIRouter
import httpx

router = APIRouter()

@router.get("/crypto")
async def get_crypto_prices():
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": "bitcoin,ethereum,solana",
                "vs_currencies": "usd",
                "include_24hr_change": "true"
            }
        )
        data = resp.json()
    
    # Format to match frontend expectations
    return [
        {"symbol": "BTCUSDT", "lastPrice": str(data["bitcoin"]["usd"]), "priceChangePercent": str(data["bitcoin"]["usd_24h_change"])},
        {"symbol": "ETHUSDT", "lastPrice": str(data["ethereum"]["usd"]), "priceChangePercent": str(data["ethereum"]["usd_24h_change"])},
        {"symbol": "SOLUSDT", "lastPrice": str(data["solana"]["usd"]), "priceChangePercent": str(data["solana"]["usd_24h_change"])}
    ]
