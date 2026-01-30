
import os
import requests
from dotenv import load_dotenv
from flipper_service import get_zip_centroid

load_dotenv()

API_KEY = os.getenv("REALIE_API_KEY")
BASE_URL = "https://app.realie.ai/api/public"
ZIP = "95130"

def verify_pagination():
    lat, lon = get_zip_centroid(ZIP)
    
    url = f"{BASE_URL}/premium/comparables/"
    headers = {'Authorization': API_KEY, 'Content-Type': 'application/json'}
    
    # Request 1: Offset 0
    params1 = {
        'latitude': lat,
        'longitude': lon,
        'radius': 10.0,
        'time_frame': 48,
        'limit': 25,
        'offset': 0
    }
    
    # Request 2: Offset 25
    params2 = {
        'latitude': lat,
        'longitude': lon,
        'radius': 10.0,
        'time_frame': 48,
        'limit': 25,
        'offset': 25
    }
    
    print("--- Testing Pagination ---")
    try:
        r1 = requests.get(url, headers=headers, params=params1)
        d1 = r1.json().get('comparables', [])
        print(f"Page 1 (Offset 0): {len(d1)} items")
        if d1:
            print(f"  First: {d1[0].get('address')}")
            print(f"  Last:  {d1[-1].get('address')}")
            
        r2 = requests.get(url, headers=headers, params=params2)
        d2 = r2.json().get('comparables', [])
        print(f"Page 2 (Offset 25): {len(d2)} items")
        if d2:
            print(f"  First: {d2[0].get('address')}")
            
        # Compare
        if d1 and d2:
            if d1[0].get('address') == d2[0].get('address'):
                print("❌ Pagination FAILED: Page 2 is identical to Page 1 (Offset ignored).")
            else:
                print("✅ Pagination WORKED: Page 2 has different content!")
        else:
            print("⚠️ Insufficient data to verify.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_pagination()
