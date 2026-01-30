
import os
import requests
from dotenv import load_dotenv
from get_comps import get_coordinates, parse_address_string

load_dotenv()
API_KEY = os.getenv("REALIE_API_KEY")
ADDR = "2048 Mayfield Ave, San Jose, CA 95130"

def test_pagination():
    print(f"--- Pagination Test ---")
    parsed = parse_address_string(ADDR)
    coords, err = get_coordinates(ADDR, parsed, API_KEY)
    
    if isinstance(coords, tuple):
        lat, lon = coords
    else:
        lat = coords['lat']
        lon = coords['lon']
        
    url = "https://app.realie.ai/api/public/premium/comparables/"
    headers = {'Authorization': API_KEY, 'Content-Type': 'application/json'}
    
    # Page 1
    p1_params = {
        'latitude': lat,
        'longitude': lon,
        'radius': 50.0, 
        'time_frame': 48,
        'limit': 25,
        'offset': 0
    }
    r1 = requests.get(url, headers=headers, params=p1_params)
    data1 = r1.json().get('comparables', [])
    ids1 = [c.get('id') for c in data1]
    print(f"Page 1: {len(data1)} items. First ID: {ids1[0] if ids1 else 'None'}")
    
    # Page 2
    p2_params = {
        'latitude': lat,
        'longitude': lon,
        'radius': 50.0, 
        'time_frame': 48,
        'limit': 25,
        'offset': 25
    }
    r2 = requests.get(url, headers=headers, params=p2_params)
    data2 = r2.json().get('comparables', [])
    ids2 = [c.get('id') for c in data2]
    print(f"Page 2: {len(data2)} items. First ID: {ids2[0] if ids2 else 'None'}")
    
    # Compare
    if not ids1 or not ids2:
        print("No data returned for one or both pages.")
        return

    if ids1 == ids2:
        print("FAIL: Page 1 and Page 2 are identical. Offset not supported.")
    else:
        print("SUCCESS: Page 2 is different. Pagination works!")
        
    # Check intersection
    overlap = set(ids1).intersection(set(ids2))
    print(f"Overlap Count: {len(overlap)}")

if __name__ == "__main__":
    test_pagination()
