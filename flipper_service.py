
import os
import requests
from datetime import datetime, timedelta
import pgeocode

# Constants
BASE_URL = "https://app.realie.ai/api/public"

def get_zip_centroid(zip_code):
    """
    Returns (lat, lon) for a given US zip code using pgeocode.
    """
    nomi = pgeocode.Nominatim('us')
    info = nomi.query_postal_code(zip_code)
    
    if info.empty or not info.latitude or str(info.latitude) == 'nan':
        return None, None
        
    return info.latitude, info.longitude

def find_flips(zip_code, api_key, radius=2.5, max_results=100, max_months=18):
    """
    Finds properties in a zip code that were bought and sold within 'max_months'.
    Returns a list of flip objects.
    Radius 2.5mi is optimal to fill the API's limit (approx 25-50) with relevant zip data.
    """
    if not api_key:
        return [], "API Key Missing"

    # 1. Get Coordinates for Zip
    lat, lon = get_zip_centroid(zip_code)
    if not lat:
        return [], f"Could not determine coordinates for Zip {zip_code}."

    # 2. Fetch Comps (4 Years)
    url = f"{BASE_URL}/premium/comparables/"
def fetch_flips_at_point(lat, lon, api_key, radius):
    try:
        url = f"{BASE_URL}/premium/comparables/"
        params = {
            'latitude': lat,
            'longitude': lon,
            'radius': radius,
            'time_frame': 48, # Always fetch 4 years history
            'limit': 50
        }
        headers = {'Authorization': api_key, 'Content-Type': 'application/json'}
        r = requests.get(url, headers=headers, params=params)
        data = r.json().get('comparables', [])
        return data, None
    except Exception as e:
        return [], str(e)

def find_flips_via_magic_search(zip_code, api_key, limit=100, days_back=550):
    """
    Uses the 'Magic' /property/search endpoint to find all properties 
    transferred within the last X days in a specific Zip Code.
    Replaces the expensive Grid Scan.
    """
    if not api_key:
        return [], "API Key Missing"
        
    url = f"https://app.realie.ai/api/public/property/search"
    
    # Check CA state default or parsed? Assuming CA for now generally or Extract from zip if possible. 
    # But simplicity: The user just gave zip in example. I will use State=CA for safety or rely on pgeocode if needed? 
    # Realie requires state? User sample has "state": "CA".
    # Let's default to CA but ideally we should parse it. 
    # For now, I will hardcode CA as this is a CA-centric bot per prompt context? 
    # Actually, let's just pass CA.
    
    params = {
        "state": "CA",
        "zipCode": zip_code,
        "limit": str(limit),
        "transferedSince": str(days_back)
    }
    
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    
    # Pagination: Scan up to 3 pages (300 items)
    all_properties = []
    current_offset = 0
    
    for page in range(3):
        # Params updates
        params["offset"] = str(current_offset)
        
        try:
            r = requests.get(url, headers=headers, params=params)
            data = r.json()
            # Verified 'properties' key from inspection
            batch = data.get('properties', [])
            if not batch:
                break
            all_properties.extend(batch)
            current_offset += limit
            
        except Exception as e:
            # If error on page 1, return error. Else just stop and process what we have.
            if page == 0:
                return [], str(e)
            break
            
    verified_flips = []
    
    for c in all_properties:
        # Root object is the LATEST sale
        sale1_date_str = str(c.get('transferDate', ''))
        sale1_price = float(c.get('transferPrice', 0) or 0)
        
        try:
            s1_date = datetime.strptime(sale1_date_str, "%Y%m%d")
        except ValueError:
            continue
            
        history = c.get('transfers', [])
        if not history: continue
        
        prior_sales = []
        for h in history:
            h_date_str = str(h.get('transferDate', ''))
            try:
                h_date = datetime.strptime(h_date_str, "%Y%m%d")
                prior_sales.append({
                    'date': h_date,
                    'price': float(h.get('transferPrice', 0) or 0),
                    'type': h.get('transferDocType'),
                    'grantee': h.get('grantee')
                })
            except ValueError: continue
        
        prior_sales.sort(key=lambda x: x['date'], reverse=True)
        
        valid_prior = None
        for p in prior_sales:
            # Find first sale strictly BEFORE the latest sale
            if p['date'] < s1_date:
                valid_prior = p
                break
        
        if valid_prior:
            delta = s1_date - valid_prior['date']
            days_held = delta.days
            months_held = days_held / 30.0
            
            # 3. TIME CHECK: 90 < days < 550 (User Defined)
            if 90 < days_held < 550:
                buy_price = float(valid_prior['price'] or 0)
                sell_price = float(sale1_price or 0)
                
                # 4. SPREAD CHECK REMOVED - Accept any spread
                if buy_price > 0:
                    profit = sell_price - buy_price
                    margin = (profit / buy_price) * 100
                    
                    # 5. ENTITY CHECK (Bonus Signal)
                    prior_grantee = str(valid_prior.get('grantee', '')).upper()
                    if "LLC" in prior_grantee or "CORP" in prior_grantee or "INC" in prior_grantee:
                        flip_type = "Corporate Flip"
                    else:
                        
                        flip_type = "Personal Flip"
                    
                    verified_flips.append({
                        'address': c.get('addressFull', c.get('address', 'Unknown')),
                        'sold_date': s1_date.strftime("%Y-%m-%d"),
                        'sold_price': sale1_price,
                        'bought_date': valid_prior['date'].strftime("%Y-%m-%d"),
                        'bought_price': valid_prior['price'],
                        'hold_months': round(months_held, 1),
                        'profit': profit,
                        'margin': round(margin, 1),
                        'sqft': c.get('buildingArea'),
                        'type': flip_type,
                        'flipper_name': prior_grantee
                    })

    # Sort by recent sales
    verified_flips.sort(key=lambda x: x['sold_date'], reverse=True)
    return verified_flips, None

def find_flips(zip_code, api_key, radius=2.5, max_results=100, max_months=18):
    """
    Finds properties in a zip code that were bought and sold within 'max_months'.
    Returns a list of flip objects.
    Radius 2.5mi is optimal to fill the API's limit (approx 25-50) with relevant zip data.
    """
    # 1. Get Coordinates for Zip
    lat, lon = get_zip_centroid(zip_code)
    if not lat:
        return [], f"Could not determine coordinates for Zip {zip_code}."

    # 2. Call Core Logic with Zip Restriction
    # Enforce 18 months (550 days) for Optimized Search
    return find_flips_by_coords(lat, lon, api_key, radius, max_results, max_months=18, restrict_to_zip=zip_code)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    API_KEY = os.getenv("REALIE_API_KEY")
    ZIP = "95135"  # San Jose / Evergreen
    
    print(f"Searching for flips in {ZIP}...")
    results, err = find_flips(ZIP, API_KEY)
    
    if err:
        print(f"Error: {err}")
    else:
        print(f"Found {len(results)} potential flips.")
        for f in results:
            print(f"- {f['address']}")
            print(f"  Bought: ${f['bought_price']} on {f['bought_date']}")
            print(f"  Sold:   ${f['sold_price']} on {f['sold_date']}")
            print(f"  Hold: {f['hold_months']} months | Gross Profit: ${f['profit']:,.0f}")
            print("-" * 20)
