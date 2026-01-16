import os
import requests
import streamlit as st

# RentCast API Configuration
BASE_URL = "https://api.rentcast.io/v1"

def get_rentcast_sales_comps(address, api_key, radius=1.0, limit=20, days_old=1000):
    """
    Fetches sales comparables from RentCast API using the /avm/value endpoint.
    Returns the 'comparables' list from the JSON response.
    """
    if not api_key:
        return None, None, "RentCast API Key is missing."

    # Updated to use Listings Endpoint for "Pending" status as requested
    url = f"{BASE_URL}/listings/sale"
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    params = {
        "address": address,
        "radius": radius,
        "status": "Pending", # Explicitly request Pending
        "daysOld": days_old, # User requested ~3 years (1000 days)
        "limit": limit
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Listings endpoint returns a list of listing objects directly
        # [ { ... }, { ... } ]
        # It does NOT return a wrapper object with "comparables" or "value"
        
        # We need to adapt the return format to match what app.py expects
        # app.py expects: (comps_list, subject_data, error)
        
        # Listings don't provide subject data (sqft etc) in the response root.
        # However, we might find the subject itself if it was listed? Unlikely/Unreliable.
        # We will return None for subject_data and let app.py handle it (it already prefers Realie subject data).
        
        # Also need to normalize keys? 
        # app.py uses: price, squareFootage, bedrooms, bathrooms, formattedAddress, zipCode, lastSaleDate (or date)
        # Listings endpoint has: price, squareFootage, bedrooms, bathrooms, formattedAddress, zipCode, listedDate
        
        return data, None, None
        
    except requests.exceptions.HTTPError as e:
        return None, None, f"RentCast API Error: {e}"
    except requests.exceptions.RequestException as e:
        return None, None, f"RentCast API Error: {str(e)}"
    except ValueError:
        return None, None, "Failed to parse RentCast response."
    except Exception as e:
        return None, None, f"An unexpected error occurred: {e}"
