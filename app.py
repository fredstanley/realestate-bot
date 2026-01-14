import streamlit as st
import os
import pandas as pd
from get_comps import find_comps

# Page Config
st.set_page_config(page_title="Realie.ai Comps Finder", page_icon="🏠")

# Title and Description
st.title("🏠 Real Estate Comps Finder")
st.markdown("Find the top 5 comparable properties (sold in the last 2 years) using **Realie.ai**.")

# Sidebar for API Key
with st.sidebar:
    st.header("Settings")
    api_key_input = st.text_input("Realie API Key", type="password", value=os.getenv("REALIE_API_KEY", ""))
    if not api_key_input:
        st.warning("Please enter your API Key to proceed.")

# Main Input
address_input = st.text_input("Enter Property Address", placeholder="e.g. 2048 Mayfield Ave, San Jose, CA 95130", help="Format: Street, City, State Zip")

if st.button("Find Comps", type="primary"):
    if not api_key_input:
        st.error("API Key is missing!")
    elif not address_input:
        st.error("Please enter an address.")
    else:
        with st.spinner("Fetching comps..."):
            comps, error = find_comps(address_input, api_key_input)
            
            if error:
                st.error(error)
            elif not comps:
                st.info("No comps found matching the criteria (Last 2 years, Same Zip Code).")
            else:
                st.success(f"Found {len(comps)} comps!")
                
                # Display metrics for the best comp
                best_comp = comps[0]
                col1, col2, col3 = st.columns(3)
                col1.metric("Closest Match Price", f"${best_comp['price']:,}")
                col2.metric("Date Sold", best_comp['date'])
                col3.metric("Distance", f"{best_comp['distance']} miles")
                
                # Create DataFrame for display
                df = pd.DataFrame(comps)
                # Reorder/Rename columns for display
                display_df = df[[
                    "address", "price", "date", "sqft", "beds", "baths", "distance"
                ]].copy()
                
                display_df.columns = ["Address", "Sold Price", "Date Sold", "SqFt", "Beds", "Baths", "Dist (mi)"]
                
                # Format price column
                # display_df["Sold Price"] = display_df["Sold Price"].apply(lambda x: f"${x:,}" if isinstance(x, (int, float)) else x)

                st.dataframe(display_df, use_container_width=True)
                
                # Map view (optional, if lat/lon were preserved in output)
                # For now just list view
