
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("REALIE_API_KEY")
BASE_URL = "https://app.realie.ai/api/public"

def debug_phillips():
    # Use the property search endpoint to find the specific property
    url = f"{BASE_URL}/property/search"
    headers = {'Authorization': API_KEY, 'Content-Type': 'application/json'}
    params = {
        'address': '17220 Phillips Ave, Los Gatos, CA 95030',
        'limit': 1
    }
    
    print("--- Inspecting 17220 Phillips Ave ---")
    try:
        r = requests.get(url, headers=headers, params=params)
        data = r.json()
        
        # This endpoint might return a list or object depending on API. 
        # Actually /property/search returns list.
        # But wait, does it return 'transfers'? Usually need /premium/comparables or /property/details
        # I'll try to get it via /premium/comparables searching effectively for it specifically?
        # Or I can use 'get_comps' logic but just for this address?
        
        # Let's try the comparables endpoint centered on it with tiny radius to just get it (and its history)
        # assuming it sold recently.
        # Comps endpoint returns 'transfers'.
        
        # First get coords for it? Or just assume I can pass address to comps? No, comps takes LatLon.
        # I'll use the search response to get lat/lon first.
        
        props = data.get('data', []) # Assuming standard structure
        if not props:
            # Try raw list if not in data
            if isinstance(data, list): props = data
            
        if not props:
            print("Property not found via search.")
            return

        target = props[0]
        lat = target.get('latitude')
        lon = target.get('longitude')
        print(f"Located: {lat}, {lon}")
        
        # Now fetch it as a 'comp' to see history (since comps endpoint includes transfers)
        comp_url = f"{BASE_URL}/premium/comparables/"
        c_params = {
            'latitude': lat,
            'longitude': lon,
            'radius': 0.1, # Tiny radius
            'time_frame': 48,
            'limit': 5
        }
        
        r2 = requests.get(comp_url, headers=headers, params=c_params)
        d2 = r2.json().get('comparables', [])
        
        found = None
        for c in d2:
            if '17220' in c.get('address', ''):
                found = c
                break
        
        if found:
            print(f"Found in sales history data: {found.get('address')}")
            transfers = found.get('transfers', [])
            print(f"Transfers ({len(transfers)}):")
            for t in transfers:
                print(f"  - Date: {t.get('transferDate')} | Price: ${t.get('transferPrice')} | Type: {t.get('transferDocType')}")
                
            # Simulate flip check
            from datetime import datetime
            s1_date = datetime.strptime(str(found.get('transferDate')), "%Y%m%d")
            print(f"Recent Sale: {s1_date.date()}")
            
            for t in transfers:
                try:
                    t_date = datetime.strptime(str(t.get('transferDate')), "%Y%m%d")
                    if t_date < s1_date:
                        months = (s1_date - t_date).days / 30.0
                        print(f"  > Prior Sale {t_date.date()} -> Hold: {months:.1f} months")
                except:
                    pass
        else:
            print("Property not found in recent sales (comparables) list.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_phillips()
