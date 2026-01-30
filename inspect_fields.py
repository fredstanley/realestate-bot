
import os
import requests
import json
from dotenv import load_dotenv
from flipper_service import get_zip_centroid

load_dotenv()

API_KEY = os.getenv("REALIE_API_KEY")
BASE_URL = "https://app.realie.ai/api/public"
ZIP = "95130"

def inspect_fields():
    lat, lon = get_zip_centroid(ZIP)
    
    url = f"{BASE_URL}/premium/comparables/"
    headers = {'Authorization': API_KEY, 'Content-Type': 'application/json'}
    params = {
        'latitude': lat,
        'longitude': lon,
        'radius': 2.0,
        'time_frame': 24,
        'limit': 5
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        comps = data.get('comparables', [])
        
        if comps:
            c = comps[0]
            print("--- Property Fields ---")
            print(json.dumps(c, indent=2))
            
            if 'transfers' in c:
                print("\n--- Transfer Fields ---")
                t = c['transfers'][0]
                print(json.dumps(t, indent=2))
            else:
                print("No transfers found in first comp.")
        else:
            print("No comps found.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_fields()
