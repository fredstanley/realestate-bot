import os
import requests
import json
import sys

# Get API Key
API_KEY = os.getenv("REALIE_API_KEY", "YOUR_REALIE_API_KEY_HERE")
BASE_URL = "https://app.realie.ai/api/public"

def get_raw_comp(full_address):
    # 1. Search for property to get coords
    print(f"Searching for: {full_address}")
    url_search = f"{BASE_URL}/property/search/"
    headers = {'Authorization': API_KEY, 'Content-Type': 'application/json'}
    
    # Parse address minimally
    parts = [p.strip() for p in full_address.split(',')]
    if len(parts) < 3:
        print("Address format error")
        return

    address = parts[0]
    # Simple parse for state (assuming last part has state zip)
    last = parts[-1].strip().split()
    if len(last) >= 2:
        state = last[0]
    else:
        state = "CA" # Fallback
        
    params = {'address': address, 'state': state, 'limit': 1}
    
    try:
        resp = requests.get(url_search, headers=headers, params=params)
        if resp.status_code != 200:
            print(f"Search Error: {resp.status_code} {resp.text}")
            return
            
        data = resp.json()
        props = data.get('properties', [])
        if not props:
            print("No properties found")
            return
            
        prop = props[0]
        lat = prop.get('latitude')
        lon = prop.get('longitude')
        print(f"Found property: {prop.get('address')} at {lat}, {lon}")
        
        print("\n--- SUBJECT PROPERTY RAW DATA ---")
        print(json.dumps(prop, indent=2))
        print("---------------------------------\n")
                
        # 2. Get Comps
        url_comps = f"{BASE_URL}/premium/comparables/"
        c_params = {
            'latitude': lat,
            'longitude': lon,
            'radius': 1,
            'time_frame': 24, # 24 months
            'max_results': 1
        }
        
        resp_c = requests.get(url_comps, headers=headers, params=c_params)
        if resp_c.status_code != 200:
            print(f"Comps Error: {resp_c.status_code} {resp_c.text}")
            return
            
        c_data = resp_c.json()
        comps = c_data.get('comparables', [])
        if not comps:
            print("No comps found")
            return
            
        print("\nFirst Comp Data Structure keys:")
        comp = comps[0]
        # print all keys that might be relevant
        print(json.dumps(comp, indent=2))
        
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        get_raw_comp(sys.argv[1])
    else:
        sys.argv.append("2048 Mayfield Ave, San Jose, CA 95130")
        get_raw_comp("2048 Mayfield Ave, San Jose, CA 95130")
