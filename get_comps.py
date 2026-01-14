import os
import requests
from datetime import datetime, timedelta
import json

# PLACEHOLDERS
API_KEY = os.getenv("REALIE_API_KEY", "YOUR_REALIE_API_KEY_HERE")
BASE_URL = "https://app.realie.ai/api/public"

def parse_address_string(full_address):
    """
    Attempts to parse a comma-separated address string.
    Expected format: "123 Main St, City, State 12345"
    Returns a dict with address, city, state, zip_code.
    """
    parts = [p.strip() for p in full_address.split(',')]
    if len(parts) < 3:
        # Fallback/Approximation
        return None
    
    address_line = parts[0]
    city = parts[1]
    last_part = parts[2]
    
    # Try to extract state and zip
    state_zip = last_part.split()
    if len(state_zip) >= 2:
        state = state_zip[0]
        zip_code = state_zip[1]
    else:
        state = last_part
        zip_code = None
        
    return {
        "address": address_line,
        "city": city,
        "state": state,
        "zip_code": zip_code
    }

CACHE_FILE = ".coords_cache.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}

def save_cache(cache):
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
    except IOError:
        pass

def get_coordinates(full_address, address_dict, api_key):
    """
    Fetches property coordinates using the Property Search endpoint.
    Checks local cache first to save API calls.
    """
    cache = load_cache()
    if full_address in cache:
        print("DEBUG: Using cached coordinates.")
        return tuple(cache[full_address]), None

    url = f"{BASE_URL}/property/search/"
    headers = {
        'Authorization': api_key, # API key directly in header as per docs
        'Content-Type': 'application/json'
    }
    
    # Docs require 'state'. 'address' is street only.
    params = {
        'state': address_dict['state'],
        'address': address_dict['address'],
        'limit': 1
    }
    if address_dict.get('city'):
        params['city'] = address_dict['city']
    if address_dict.get('zip_code'):
        params['zip_code'] = address_dict['zip_code']

    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            properties = data.get('properties', [])
            if not properties:
                return None, "No property found for this address."
            
            # Assuming the first result is the correct one
            prop = properties[0]
            lat = prop.get('latitude')
            lon = prop.get('longitude')
            
            if not lat or not lon:
                return None, "Property found but has no coordinates."
            
            # Save to cache
            cache[full_address] = (lat, lon)
            save_cache(cache)
                
            return (lat, lon), None
        else:
            return None, f"Property API Error: {response.status_code} - {response.text}"
    except requests.exceptions.RequestException as e:
        return None, f"Property Request Error: {e}"

def get_comps(lat, lon, api_key):
    """
    Fetches comps using the Premium Comparables Search endpoint.
    """
    url = f"{BASE_URL}/premium/comparables/"
    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json'
    }
    
    params = {
        'latitude': lat,
        'longitude': lon,
        'radius': 1,        # Default 1 mile
        'time_frame': 24,   # 2 years (24 months)
        'max_results': 5
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            comps = data.get('comparables', [])
            return comps, None
        else:
            return None, f"Comps API Error: {response.status_code} - {response.text}"
    except requests.exceptions.RequestException as e:
        return None, f"Comps Request Error: {e}"

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    import math
    # Convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])

    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 3956 # Radius of earth in miles. Use 6371 for km
    return c * r

def find_comps(full_address, api_key):
    """
    Orchestrates the comps search process:
    1. Parse Address
    2. Get Coordinates (w/ caching)
    3. Get Comps
    4. Filter by Date (2 years) and Zip Code (School proxy)
    5. Return formatted list
    """
    comps_data = []
    
    # 1. Parse
    parsed = parse_address_string(full_address)
    if not parsed:
        return None, "Error: Could not parse address. Please use format: 'Address, City, State Zip'"
    
    # 2. Coordinates
    coords, error = get_coordinates(full_address, parsed, api_key)
    if error:
        return None, f"Coordinate Error: {error}"
    
    lat, lon = coords
    
    # 3. Comps
    raw_comps, error = get_comps(lat, lon, api_key)
    if error:
        return None, f"Comps Error: {error}"
        
    if not raw_comps:
        return [], None

    # 4. Filter and Format
    valid_comps = []
    two_years_ago = datetime.now() - timedelta(days=365*2)
    target_zip = parsed.get('zip_code')

    for comp in raw_comps:
        # Date Filter
        date_str = str(comp.get('transferDate', ''))
        try:
            sale_date = datetime.strptime(date_str, "%Y%m%d")
        except ValueError:
            continue
            
        if sale_date < two_years_ago:
            continue
            
        # Zip Filter
        comp_zip = comp.get('zipCode')
        if target_zip and comp_zip != target_zip:
            continue
            
        # Calculate Distance
        dist_val = float('inf')
        dist_str = "N/A"
        c_lat = comp.get('latitude')
        c_lon = comp.get('longitude')
        if c_lat and c_lon:
            try:
                dist_val = haversine(lat, lon, float(c_lat), float(c_lon))
                dist_str = f"{dist_val:.2f}"
            except (ValueError, TypeError):
                pass

        # Format for output
        formatted_comp = {
            "address": comp.get('address', 'N/A'),
            "price": comp.get('transferPrice', 'N/A'),
            "date": sale_date.strftime("%Y-%m-%d"),
            "sqft": comp.get('buildingArea', 'N/A'),
            "beds": comp.get('totalBedrooms', 'N/A'),
            "baths": comp.get('totalBathrooms', 'N/A'),
            "distance": dist_str,
            "_raw_date": sale_date,
            "dist_val": dist_val
        }
        valid_comps.append(formatted_comp)

    # Sort by date descending
    valid_comps.sort(key=lambda x: x['_raw_date'], reverse=True)
    
    return valid_comps[:5], None

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 get_comps.py \"123 Main St, City, State Zip\"")
        print("Example: python3 get_comps.py \"2048 Mayfield Ave, San Jose, CA 95130\"")
        sys.exit(1)
        
    full_address = sys.argv[1]
    print(f"Processing: {full_address}")
    
    comps, error = find_comps(full_address, API_KEY)
    
    if error:
        print(error)
        sys.exit(1)
        
    if not comps:
        print("No comps found.")
        return

    print(f"\n--- Top {len(comps)} Comps (Last 2 Years, Same Zip Code) ---")
    
    for i, comp in enumerate(comps, 1):
        print(f"{i}. {comp['address']}")
        print(f"   Sold: ${comp['price']} on {comp['date']}")
        print(f"   Size: {comp['sqft']} sqft | {comp['beds']} Beds / {comp['baths']} Baths")
        print(f"   Dist: {comp['distance']} miles\n")

if __name__ == "__main__":
    main()
