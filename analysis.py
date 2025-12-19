import os
import httpx
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

HELIUS_API_KEY = os.getenv('HELIUS_API_KEY')
BASE_URL = f"https://api.helius.xyz/v0/addresses/{{address}}/transactions?api-key={HELIUS_API_KEY}"

async def get_wallet_profile(address: str):
    """
    Analyzes wallet age, behavior, and basic PNL using Helius API.
    """
    if not HELIUS_API_KEY:
        return {"error": "Helius API Key not found"}

    url = BASE_URL.format(address=address)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            transactions = response.json()
            
            if not transactions:
                return {"style": "New", "age": 0, "volume": 0}

            # 1. Wallet Age
            last_tx = transactions[-1]
            first_tx_time = datetime.fromtimestamp(last_tx['timestamp'])
            age_days = (datetime.utcnow() - first_tx_time).days
            
            # 2. Behavior Analysis (Basic)
            tx_count = len(transactions)
            buy_count = sum(1 for tx in transactions if 'tokenTransfers' in tx and any(t['toUser'] == address for t in tx['tokenTransfers']))
            sell_count = sum(1 for tx in transactions if 'tokenTransfers' in tx and any(t['fromUser'] == address for t in tx['tokenTransfers']))
            
            style = "Unknown"
            if tx_count > 50 and sell_count / tx_count > 0.4:
                style = "Active Trader/Swing"
            elif tx_count < 10 and age_days > 30:
                style = "Diamond Hand/Holder"
            elif tx_count > 100:
                style = "High Frequency/Bot"
            else:
                style = "Regular Trader"

            # 3. PNL / Volume (Simplified)
            total_sol_in = sum(float(tx['nativeTransfers'][0]['amount']) for tx in transactions if 'nativeTransfers' in tx and tx['nativeTransfers'] and tx['nativeTransfers'][0]['toUser'] == address) / 1e9
            
            return {
                "wallet_address": address,
                "wallet_age_days": age_days,
                "total_volume_sol": round(total_sol_in, 2),
                "trading_style": style,
                "win_rate": 0.5, # Placeholder for more complex logic
                "last_updated": datetime.utcnow()
            }

        except Exception as e:
            print(f"Error fetching Helius data for {address}: {e}")
            return None

if __name__ == "__main__":
    import asyncio
    # Test with a known whale or user address
    # asyncio.run(get_wallet_profile("..."))
    pass
