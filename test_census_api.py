import requests
import json

def check_census_district(lat, lon):
    url = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
    params = {
        'x': lon,
        'y': lat,
        'benchmark': 'Public_AR_Current',
        'vintage': 'Current_Current',
        'layers': 'Unified School Districts,Secondary School Districts,Elementary School Districts',
        'format': 'json'
    }
    
    try:
        response = requests.get(url, params=params)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            # print(json.dumps(data, indent=2))
            
            geographies = data.get('result', {}).get('geographies', {})
            print("\nFound Geographies:")
            found = False
            for layer_name, items in geographies.items():
                if 'School Districts' in layer_name:
                    for item in items:
                        print(f"- {layer_name}: {item.get('NAME')} (ID: {item.get('GEOID')})")
                        found = True
            
            if not found:
                print("No School District layers found.")
                print("Available layers:", list(geographies.keys()))

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # 2048 Mayfield Ave, San Jose, CA 95130
    # Lat: 37.28466, Lon: -121.98710 (Approx)
    lat = 37.28466
    lon = -121.98710
    check_census_district(lat, lon)
