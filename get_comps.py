import os
import requests
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv

load_dotenv()

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
        cached_val = cache[full_address]
        # Legacy tuple check
        if isinstance(cached_val, list) and len(cached_val) == 2: # JSON loads tuple as list
             return {'lat': cached_val[0], 'lon': cached_val[1], 'sqft': None}, None
        return cached_val, None

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
            
            # Save to cache (store full prop details or just coords + sqft?)
            # To minimize breakage, let's keep cache format simple but extend return
            # Cache: {address: {'lat': lat, 'lon': lon, 'sqft': buildingArea}}
            
            # Since existing cache is tuple, we might need to handle migration or valid check
            # For simplicity, let's just update the return for now and handle cache structure
            
            prop_data = {
                'lat': lat,
                'lon': lon,
                'sqft': prop.get('buildingArea'),
                'details': prop # Store full prop if needed later
            }
            
            # Update cache logic later if needed, for now just return data
            # return (lat, lon), None <--- OLD
            return prop_data, None
        else:
            return None, f"Property API Error: {response.status_code} - {response.text}"
    except requests.exceptions.RequestException as e:
        return None, f"Property Request Error: {e}"

def get_comps(lat, lon, radius, api_key):
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
        'radius': radius,
        'time_frame': 36,   # 3 years (36 months)
        'max_results': 50   # Dump all (up to 50)
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

def get_school_districts(lat, lon):
    """
    Fetches school district information from the US Census Bureau Geocoding API.
    Returns a set of district IDs/Names to use for comparison.
    """
    url = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
    params = {
        'x': lon,
        'y': lat,
        'benchmark': 'Public_AR_Current',
        'vintage': 'Current_Current',
        'layers': 'Unified School Districts,Secondary School Districts,Elementary School Districts',
        'format': 'json'
    }
    
    districts = {}
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            geographies = data.get('result', {}).get('geographies', {})
            
            for layer_name, items in geographies.items():
                if 'School Districts' in layer_name:
                    # Use the first item found for the layer (usually only one district per level)
                    if items:
                        item = items[0]
                        # Key by layer type (e.g., 'Elementary School Districts')
                        # Value is the GEOID which is unique, or NAME
                        districts[layer_name] = {
                            'name': item.get('NAME', ''),
                            'id': item.get('GEOID', '')
                        }
        return districts, None
    except Exception as e:
        return None, f"Census API Error: {e}"

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

def find_comps(full_address, radius, api_key):
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
        return None, None, "Error: Could not parse address. Please use format: 'Address, City, State Zip'"
    
    # 2. Coordinates
    prop_data, error = get_coordinates(full_address, parsed, api_key)
    if error:
        return None, None, f"Coordinate Error: {error}"
    
    # Handle legacy cache tuple if present, or new dict
    if isinstance(prop_data, tuple):
        lat, lon = prop_data
        subject_sqft = None # Legacy cache might not have sqft
        print("Warning: Using legacy cache format (no sqft filtering).")
        # You could force-refresh cache here if critical
    else:
        lat = prop_data['lat']
        lon = prop_data['lon']
        subject_sqft = prop_data.get('sqft')

    print(f"Subject SqFt: {subject_sqft}")
    
    # 3. Comps
    raw_comps, error = get_comps(lat, lon, radius, api_key)
    # ... (rest of comps fetching)
    if not raw_comps:
        return [], [], None

    # 4. Filter and Format
    valid_comps = []
    # Changed to 3 years as per user request
    three_years_ago = datetime.now() - timedelta(days=365*3)
    target_zip = parsed.get('zip_code')

    for comp in raw_comps:
        # Date Filter
        date_str = str(comp.get('transferDate', ''))
        try:
            sale_date = datetime.strptime(date_str, "%Y%m%d")
        except ValueError:
            continue
            
        if sale_date < three_years_ago:
            continue
            
        # Zip Filter
        comp_zip = comp.get('zipCode')
        if target_zip and comp_zip != target_zip:
            continue

        # Residential Filter (Exclude explicitly non-residential)
        if comp.get('residential') is False:
             continue

        # Transaction Type Filter (Exclude non-market transfers)
        # User requested to see OFF MARKET sales which might be 'IT'
        doc_type = comp.get('transferDocType', '')
        # if doc_type in ['IT', 'QD']:
        #     continue
            
        # SqFt Filter (+/- 300 sqft)
        c_sqft = comp.get('buildingArea')
        if subject_sqft and c_sqft:
            try:
                s_sqft_val = float(subject_sqft)
                c_sqft_val = float(c_sqft)
                if abs(s_sqft_val - c_sqft_val) > 500:
                    # print(f"DEBUG: Skipping {comp.get('address')} (SqFt: {c_sqft} vs Subject: {subject_sqft})")
                    continue
            except (ValueError, TypeError):
                pass 

        # Price Filter (Exclude low-value transfers < $500k)
        # This excludes "Paperwork" transfers (like Falls Creek) while keeping "Off-Market" sales (like Adelanto)
        try:
            price = float(comp.get('transferPrice', 0) or 0)
        except (ValueError, TypeError):
            price = 0
            
        if price < 500000:
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
            "dist_val": dist_val,
            "_lat": comp.get('latitude'),
            "_lon": comp.get('longitude')
        }
        valid_comps.append(formatted_comp)

    # Sort by date descending
    valid_comps.sort(key=lambda x: x['_raw_date'], reverse=True)
    
    # --- Step 5: Strict School Verification (Census API) ---
    # User requested to comment out school logic for now (Task 9)
    # print(f"   > Pre-filtered to {len(valid_comps)} comps based on radius/zip/date.")
    # print("   > Verifying School Districts via US Census API (this may take a moment)...")
    
    # # Get Subject Districts
    # subj_districts, err = get_school_districts(lat, lon)
    # if err:
    #     print(f"   Warning: Could not fetch subject districts ({err}). Skipping strict school check.")
    #     return valid_comps, raw_comps, None
    
    # if not subj_districts:
    #     print("   Warning: No school districts found for subject property. Skipping strict school check.")
    #     return valid_comps, raw_comps, None
        
    # print(f"   > Subject Districts: {', '.join([d['name'] for d in subj_districts.values()])}")
    
    # verified_comps = []
    # print(f"   > Checking {len(valid_comps)} candidates...")
    
    # for i, comp in enumerate(valid_comps, 1):
    #     c_lat = comp.get('_lat')
    #     c_lon = comp.get('_lon')
    #     
    #     if not c_lat or not c_lon:
    #         print(f"     [{i}/{len(valid_comps)}] Skip {comp['address']} (Missing Coords)")
    #         continue
    #         
    #     # Get Comp Districts
    #     c_districts, err = get_school_districts(c_lat, c_lon)
    #     if err or not c_districts:
    #         print(f"     [{i}/{len(valid_comps)}] Skip {comp['address']} (District lookup failed)")
    #         continue
    #         
    #     # --- Granular Scoring Logic ---
    #     # Unified = Elem + Mid + High (3)
    #     # Elementary District = Elem + Mid (2)
    #     # Secondary District = High (1)
    #     
    #     matched_names = []
    #     matched_levels = []
    #     score = 0
    #     
    #     # Check Unified
    #     s_uni = subj_districts.get('Unified School Districts')
    #     c_uni = c_districts.get('Unified School Districts')
    #     if s_uni and c_uni and s_uni['id'] == c_uni['id']:
    #         matched_levels.extend(['Elementary', 'Middle', 'High'])
    #         matched_names.append(f"{s_uni['name']} (K-12)")
    #         score += 3
    #     else:
    #         # Check Elementary (Worth 2: Elem + Mid)
    #         s_elem = subj_districts.get('Elementary School Districts')
    #         c_elem = c_districts.get('Elementary School Districts')
    #         if s_elem and c_elem and s_elem['id'] == c_elem['id']:
    #             matched_levels.extend(['Elementary', 'Middle'])
    #             matched_names.append(f"{s_elem['name']} (Elem/Mid)")
    #             score += 2
    #             
    #         # Check Secondary (Worth 1: High)
    #         s_sec = subj_districts.get('Secondary School Districts')
    #         c_sec = c_districts.get('Secondary School Districts')
    #         if s_sec and c_sec and s_sec['id'] == c_sec['id']:
    #             matched_levels.append('High')
    #             matched_names.append(f"{s_sec['name']} (High)")
    #             score += 1
    #     
    #     if score > 0:
    #         match_str = f"{score} Match"
    #         # if score < 3:
    #         #      match_str += f": {', '.join(matched_levels)}"
    #              
    #         print(f"     [{i}/{len(valid_comps)}] KEEP ({match_str}): {comp['address']}")
    #         
    #         comp['match_score'] = score
    #         comp['match_desc'] = match_str
    #         comp['matched_names'] = matched_names
    #         comp['districts'] = [d['name'] for d in c_districts.values()]
    #         verified_comps.append(comp)
    #     else:
    #         print(f"     [{i}/{len(valid_comps)}] REJECT (0 Match): {comp['address']}")

    # # Sort by Score (Desc), then by Date (Desc)
    # verified_comps.sort(key=lambda x: (x['match_score'], x['_raw_date']), reverse=True)

    # print(f"   > Verification Complete. {len(verified_comps)} comps retained.")
    
    # Bypass school verification and just return filtered comps
    verified_comps = valid_comps
    
    # --- Step 6: Outlier Filter (User Request: "500k different to remove anomalies") ---
    # Only apply if we have enough data (>= 3) to establish a baseline.
    if len(verified_comps) >= 3:
        prices = [float(c['price']) for c in verified_comps if c['price'] != 'N/A' and float(c['price']) > 0]
        if prices:
            import statistics
            median_price = statistics.median(prices)
            # Filter
            final_comps = []
            for comp in verified_comps:
                try:
                    p = float(comp['price'])
                    if abs(p - median_price) > 500000:
                        # print(f"DEBUG: Removing Outlier {comp['address']} (${p}) - Median: ${median_price}")
                        continue
                except (ValueError, TypeError):
                    pass
                final_comps.append(comp)
            verified_comps = final_comps
            
    for comp in verified_comps:
        comp['match_desc'] = "N/A"
        comp['matched_names'] = []
        
    return verified_comps, raw_comps, None

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 get_comps.py \"123 Main St, City, State Zip\"")
        print("Example: python3 get_comps.py \"2048 Mayfield Ave, San Jose, CA 95130\"")
        sys.exit(1)
        
    full_address = sys.argv[1]
    print(f"Processing: {full_address}")
    
    # Default radius 1 for CLI
    comps, raw, error = find_comps(full_address, 1, API_KEY)
    
    if error:
        print(error)
        sys.exit(1)
        
    if not comps:
        print("No comps found.")
        if raw:
             print(f"However, {len(raw)} raw comps were fetched from API.")
        return

    print(f"\n--- Found {len(comps)} Comps (Sorted by School Match, then Date) ---")
    
    for i, comp in enumerate(comps, 1):
        print(f"{i}. [{comp.get('match_desc', 'N/A')}] {comp['address']}")
        matches = comp.get('matched_names', [])
        if matches:
            print(f"   Matches: {', '.join(matches)}")
        print(f"   Sold: ${comp['price']} on {comp['date']}")
        print(f"   Size: {comp['sqft']} sqft | {comp['beds']} Beds / {comp['baths']} Baths")
        print(f"   Dist: {comp['distance']} miles\n")

if __name__ == "__main__":
    main()
