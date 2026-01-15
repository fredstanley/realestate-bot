import os
import sys
import json
from dotenv import load_dotenv
from get_comps import find_comps, get_comps, get_coordinates, parse_address_string

load_dotenv()
API_KEY = os.getenv("REALIE_API_KEY")

target_address = "3043 Rosato Ct, San Jose, CA 95135"
missing_street = "Falls Creek"

print(f"--- Inspecting Raw Comps for {target_address} ---")

# 1. Get Coords
parsed = parse_address_string(target_address)
prop_data, err = get_coordinates(target_address, parsed, API_KEY)
if err:
    print(f"Error getting coords: {err}")
    sys.exit(1)

lat = prop_data['lat']
lon = prop_data['lon']
radius = 1 # Assuming 1 mile radius captures it (User said 0.06 miles)

print(f"Subject Coords: {lat}, {lon}")

# 2. Get Raw Comps
raw_comps, err = get_comps(lat, lon, radius, API_KEY)
if err:
     print(f"Error getting comps: {err}")
     sys.exit(1)

print(f"Total Raw Comps Returned: {len(raw_comps)}")

# 3. Find missing comp
found = False
for c in raw_comps:
    addr = c.get('address', '').lower()
    if missing_street.lower() in addr:
        found = True
        print(f"\n!!! FOUND {c.get('address')} IN RAW DATA !!!")
        print(json.dumps(c, indent=2))
        
        # Check specific date fields
        print("-" * 20)
        print(f"transferDate: {c.get('transferDate')}")
        print(f"lastSaleDate: {c.get('lastSaleDate')}")
        print(f"priorTransferDate: {c.get('priorTransferDate')}")
        print("-" * 20)
        
if not found:
    print(f"\nXXX {missing_street} NOT found in raw comps list. XXX")
    print("Dumping first 3 raw comps to see structure:")
    for c in raw_comps[:3]:
        print(c.get('address'))
