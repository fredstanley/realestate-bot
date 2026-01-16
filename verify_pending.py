
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def verify_pending():
    api_key = os.getenv("RENTCAST_API_KEY")
    if not api_key:
        print("No API Key")
        return

    address = "3043 Rosato Ct, San Jose, CA 95135"
    print(f"Checking RentCast /v1/listings/sale (Pending) for: {address}")
    
    url = "https://api.rentcast.io/v1/listings/sale"
    params = {
        "address": address,
        "radius": 1.0,
        "status": "Pending", 
        "limit": 50
    }
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        comps = response.json()
    except Exception as e:
        print(f"Error: {e}")
        return

    print(f"Found {len(comps)} Pending properties.")
    
    if comps:
        print("Top 5 Pending:")
        for c in comps[:5]:
            # Properties endpoint usually has 'price' or 'listPrice'?
            # Let's print available keys for the first one to be sure
            if c == comps[0]:
                print(f"Keys: {list(c.keys())}")
            
            price = c.get('price') or c.get('listPrice')
            print(f"- {c.get('formattedAddress')}: ${price}")

if __name__ == "__main__":
    verify_pending()
