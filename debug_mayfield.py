
import os
from dotenv import load_dotenv
from get_comps import get_coordinates, parse_address_string
from flipper_service import find_flips_by_coords

load_dotenv()
API_KEY = os.getenv("REALIE_API_KEY")
ADDR = "2048 Mayfield Ave, San Jose, CA 95130"

def test_new_logic():
    print(f"--- Testing Grid Scan for {ADDR} ---")
    parsed = parse_address_string(ADDR)
    coords, err = get_coordinates(ADDR, parsed, API_KEY)
    
    if err:
        print(f"Coord Error: {err}")
        return

    if isinstance(coords, tuple):
        lat, lon = coords
    else:
        lat = coords['lat']
        lon = coords['lon']
        
    print(f"Coords: {lat}, {lon}")
    print("Starting Grid Scan (Target: 5 flips)...")
    
    # Radius shouldn't matter too much if we are moving the center interactions, 
    # but let's stick to 50 for the 'search intent'
    flips, err = find_flips_by_coords(lat, lon, API_KEY, radius=50.0)
    
    if err:
        print(f"Error: {err}")
    else:
        print(f"Found {len(flips)} flips!")
        for f in flips:
            print(f" - {f['address']} ({f['type']})")
            print(f"   Profit: ${f['profit']:,.0f} | Margin: {f['margin']}% | Hold: {f['hold_months']}m")

if __name__ == "__main__":
    test_new_logic()
