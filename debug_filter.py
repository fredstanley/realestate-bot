import os
import requests
from dotenv import load_dotenv
import math

load_dotenv()
API_KEY = os.getenv("REALIE_API_KEY")
BASE_URL = "https://app.realie.ai/api/public"

def get_property_details(address):
    url = f"{BASE_URL}/property/search/"
    headers = {'Authorization': API_KEY, 'Content-Type': 'application/json'}
    # Hardcoded for debug simplicity since we know the address structure
    # Expected format: "Address, City, State Zip"
    parts = address.split(',')
    street = parts[0].strip()
    city = parts[1].strip()
    state_zip = parts[2].strip().split()
    state = state_zip[0]
    
    params = {
        'address': street,
        'city': city,
        'state': state,
        'limit': 1
    }
    
    print(f"Fetching: {address}")
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            props = data.get('properties', [])
            if props:
                return props[0]
            else:
                print("No property found.")
                return None
        else:
            print(f"Error: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

def haversine(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 3956 
    return c * r

subject_addr = "3043 Rosato Ct" # San Jose, CA 95135
comp_addr = "3054 Silverland Dr" # San Jose, CA 95135

print("--- Subject Property ---")
subject = get_property_details("3043 Rosato Ct, San Jose, CA 95135")
if not subject:
    exit()
    
s_sqft = subject.get('buildingArea')
s_lat = subject.get('latitude')
s_lon = subject.get('longitude')

print(f"Subject SqFt: {s_sqft}")
print(f"Subject Coords: {s_lat}, {s_lon}")

print("\n--- Missing Comp ---")
comp = get_property_details("3054 Silverland Dr, San Jose, CA 95135")
if not comp:
    print("Could not find comp in API.")
else:
    c_sqft = comp.get('buildingArea')
    c_lat = comp.get('latitude')
    c_lon = comp.get('longitude')
    
    print(f"Comp SqFt: {c_sqft}")
    print(f"Comp Coords: {c_lat}, {c_lon}")
    
    # Check Filters
    print("\n--- Filter Check ---")
    
    # 1. SqFt
    if s_sqft and c_sqft:
        diff = abs(float(s_sqft) - float(c_sqft))
        print(f"SqFt Diff: {diff} (Limit: 300) -> {'PASS' if diff <= 300 else 'FAIL'}")
    else:
        print("SqFt check skipped (missing data).")
        
    # 2. Distance
    if s_lat and s_lon and c_lat and c_lon:
        dist = haversine(s_lat, s_lon, c_lat, c_lon)
        print(f"Distance: {dist:.2f} miles (Limit: 1.0 or user set) -> {'PASS' if dist <= 1.0 else 'FAIL (> 1.0)'}")
        
    # 3. Transaction Type (We can't easily check 'transferDocType' from property search, 
    # need comp search, but this gives a hint)
    print(f"Last Sale Date: {comp.get('lastSaleDate')}")
    print(f"Last Sale Price: {comp.get('lastSalePrice')}")

