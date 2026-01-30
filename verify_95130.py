
import os
import requests
from dotenv import load_dotenv
from flipper_service import get_zip_centroid

load_dotenv()

API_KEY = os.getenv("REALIE_API_KEY")
BASE_URL = "https://app.realie.ai/api/public"
ZIP = "95130"

def verify_95130():
    print(f"--- Debugging Flips for {ZIP} ---")
    
    # 1. Check Geocode
    lat, lon = get_zip_centroid(ZIP)
    print(f"1. Geocode Centroid: {lat}, {lon}")
    if not lat:
        print("❌ Geocoding Failed!")
        return

    # 2. Fetch Comps
    url = f"{BASE_URL}/premium/comparables/"
    headers = {'Authorization': API_KEY, 'Content-Type': 'application/json'}
    params = {
        'latitude': lat,
        'longitude': lon,
        'radius': 1.0, # Small radius to force local results
        'time_frame': 48,
        'limit': 100,
        'max_results': 100 
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        comps = data.get('comparables', [])
        print(f"2. Raw Comps Fetched: {len(comps)}")
        
        if not comps:
            print("❌ No comps returned from API.")
            return

        # Check what zips ARE returned
        returned_zips = set([c.get('zipCode') for c in comps])
        print(f"DEBUG: Zips present in response: {returned_zips}")

        # 3. Check Zip Filtering
        target_zip_str = str(ZIP).split('-')[0]
        zip_matches = [c for c in comps if str(c.get('zipCode', '')).split('-')[0] == target_zip_str]
        print(f"3. Comps in Zip {ZIP}: {len(zip_matches)}")
        
        # 4. Check History Availability
        with_history = [c for c in zip_matches if c.get('transfers')]
        print(f"4. Comps with 'transfers' history: {len(with_history)}")
        
        # 5. Check Flip Logic Manually on a few
        print("\n--- Inspecting first 5 candidates with history ---")
        from datetime import datetime
        
        max_months = 18
        
        for i, c in enumerate(with_history[:10]):
            sale1_date_str = str(c.get('transferDate', ''))
            try:
                s1_date = datetime.strptime(sale1_date_str, "%Y%m%d")
            except:
                continue
                
            history = c.get('transfers', [])
            prior_dates = []
            valid_prior = None
            
            for h in history:
                h_date_str = str(h.get('transferDate', ''))
                try:
                    h_date = datetime.strptime(h_date_str, "%Y%m%d")
                    prior_dates.append(h_date_str)
                    if h_date < s1_date:
                         # Check recent prior
                         if (s1_date - h_date).days / 30.0 <= 48: # Just printing recent usage
                             valid_prior = h_date
                except:
                    pass
            
            print(f"Property: {c.get('address')}")
            print(f"  Current Sale: {sale1_date_str}")
            print(f"  History Dates: {prior_dates}")
            
            if valid_prior:
                months = (s1_date - valid_prior).days / 30.0
                print(f"  > Time since last sale: {months:.1f} months")
                if months <= max_months:
                    print(f"  ✅ SHOULD BE DETECTED AS FLIP (< {max_months} mo)")
                else:
                    print(f"  ❌ Too long hold ({months:.1f} mo)")
            else:
                 print("  ❌ No prior sale found in history list (or verify parse).")
            print("-")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_95130()
