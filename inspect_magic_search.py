import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("REALIE_API_KEY")

url = "https://app.realie.ai/api/public/property/search"

headers = {
    "Authorization": api_key
}

# Testing with user's example zip, or one we know has flips like 95135 or 95130
querystring = {
    "state": "CA",
    "zipCode": "95130", # Using Mayfield Zip
    "limit": "10", 
    "transferedSince": "550" 
}

print(f"Calling {url} with params: {querystring}")
response = requests.get(url, headers=headers, params=querystring)

if response.status_code == 200:
    data = response.json()
    props = data.get('properties', [])
    print(f"Found {len(props)} properties.")
    if props:
        # Dump the first property to see fields
        print(json.dumps(props[0], indent=2))
else:
    print(f"Error: {response.status_code} - {response.text}")
