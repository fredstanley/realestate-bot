
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("REALIE_API_KEY")
BASE_URL = "https://app.realie.ai/api/public"

def get_property_details(address):
    url = f"{BASE_URL}/property/search/"
    headers = {'Authorization': API_KEY, 'Content-Type': 'application/json'}
    parts = address.split(',')
    street = parts[0].strip()
    city = parts[1].strip() if len(parts) > 1 else 'San Jose'
    state = 'CA'
    
    params = {'state': state, 'address': street, 'limit': 1, 'city': city}
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code == 200:
        props = resp.json().get('properties', [])
        if props: return props[0]
    return None

def get_comps(lat, lon, radius):
    url = f"{BASE_URL}/premium/comparables/"
    headers = {'Authorization': API_KEY, 'Content-Type': 'application/json'}
    params = {
        'latitude': lat,
        'longitude': lon,
        'radius': radius,
        'time_frame': 36,
        'max_results': 50
    }
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code == 200:
        return resp.json().get('comparables', [])
    return []

def main():
    target_addr = "15158 Charmeran Ave, San Jose, CA 95124"
    print(f"Analyzing comps for: {target_addr}")
    
    subject = get_property_details(target_addr)
    if not subject:
        print("Subject not found.")
        return
        
    s_lat = subject.get('latitude')
    s_lon = subject.get('longitude')
    s_sqft = subject.get('buildingArea')
    s_zip = subject.get('zipCode')
    
    print(f"Subject: SqFt={s_sqft}, Zip={s_zip}, Lat={s_lat}, Lon={s_lon}")
    
    raw_comps = get_comps(s_lat, s_lon, 1)
    print(f"Raw Comps: {len(raw_comps)}")
    
    three_years_ago = datetime.now() - timedelta(days=365*3)
    
    for i, c in enumerate(raw_comps):
        reason = "PASS"
        addr = c.get('address')
        
        # 1. Date
        date_str = str(c.get('transferDate', ''))
        try:
            date_obj = datetime.strptime(date_str, "%Y%m%d")
        except:
            date_obj = None
            
        if not date_obj:
            reason = "Missing Date"
        elif date_obj < three_years_ago:
            reason = f"Old Date ({date_str})"
            
        # 2. Zip
        if reason == "PASS":
            if s_zip and c.get('zipCode') != s_zip:
                reason = f"Zip Mismatch ({c.get('zipCode')})"
                
        # 3. Residential
        if reason == "PASS":
            if c.get('residential') is False:
                reason = "Not Residential"
                
        # 4. SqFt
        if reason == "PASS":
            c_sqft = c.get('buildingArea')
            if not c_sqft:
                # reason = "Missing SqFt" # Actually current code skips if missing? No, code says "if not c_sqft: continue"
                reason = "Missing SqFt"
            else:
                try:
                    curr_sqft = float(c_sqft)
                    subj_sqft_val = float(s_sqft)
                    if abs(curr_sqft - subj_sqft_val) > 500:
                        reason = f"SqFt Diff ({curr_sqft} vs {subj_sqft_val})"
                except:
                    reason = "SqFt Error"

        # 5. Price
        price = 0
        if reason == "PASS":
            try:
                price = float(c.get('transferPrice', 0) or 0)
                if price < 500000:
                    reason = f"Low Price (${price})"
            except:
                pass
                
        print(f"{i+1}. {addr}: {reason} [Price: ${price}]")

if __name__ == "__main__":
    main()
