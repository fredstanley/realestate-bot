
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def verify_days_old():
    api_key = os.getenv("RENTCAST_API_KEY")
    if not api_key:
        print("No API Key")
        return

    address = "3043 Rosato Ct, San Jose, CA 95135"  # Search center
    target = "3036 Silverland"
    
    print(f"Testing 'daysOld=1000' search for '{target}' near '{address}'")
    
    # Try Listings Endpoint with extended daysOld
    # We remove 'status=Pending' to test if the date range captures "Inactive" or "Sold" listings
    # or if we need to specify status=['Active', 'Pending', 'Inactive'] (if supported) or just broad.
    
    url = "https://api.rentcast.io/v1/listings/sale"
    
    # User requested params
    params = {
        "address": address,
        "radius": 1.0,
        "daysOld": 1000,
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
        
        print(f"Found {len(comps)} listings with daysOld=1000.")
        
        found = False
        for c in comps:
            addr = c.get('formattedAddress', '')
            status = c.get('status', 'Unknown')
            date = c.get('listedDate') or c.get('date')
            
            if target.lower() in addr.lower():
                print(f"✅ FOUND TARGET!")
                print(f"   Address: {addr}")
                print(f"   Status: {status}")
                print(f"   Date: {date}")
                print(f"   Price: {c.get('price')}")
                found = True
                break
        
        if not found:
            print(f"❌ '{target}' NOT found even with daysOld=1000.")
            print("Top 5 Results:")
            for c in comps[:5]:
                print(f"- {c.get('formattedAddress')} ({c.get('status')})")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_days_old()
