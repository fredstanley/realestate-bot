import streamlit as st
import os
import pandas as pd
import io
import contextlib
from get_comps import find_comps

# Page Config
st.set_page_config(page_title="Realie.ai Comps Finder", page_icon="🏠")

# Title and Description
st.title("🏠 Real Estate Comps Finder")
st.markdown("Find the top comp properties (sold in the last 24 months) using **Realie.ai** with Census School Verification.")

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
            # Capture stdout
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                comps, error = find_comps(address_input, api_key_input)
            
            output_log = f.getvalue()
            
            if error:
                st.error(error)
            elif not comps:
                st.info("No comps found matching the criteria (1 Mile, 24 Months, Same Zip/School).")
            else:
                st.success(f"Found {len(comps)} comps! (Sorted by School Match)")
                
                # Display metrics for the best comp
                best_comp = comps[0]
                col1, col2, col3 = st.columns(3)
                col1.metric("Closest Match Price", f"${best_comp['price']:,}")
                col2.metric("Date Sold", best_comp['date'])
                col3.metric("Distance", f"{best_comp['distance']} miles")
                
                # Create DataFrame for display
                df = pd.DataFrame(comps)
                
                # Expand matched names to string
                df['matches_str'] = df['matched_names'].apply(lambda x: ', '.join(x) if isinstance(x, list) else "")
                
                # Reorder/Rename columns for display
                display_df = df[[
                    "address", "price", "date", "sqft", "beds", "baths", "distance", "match_desc", "matches_str"
                ]].copy()
                
                display_df.columns = ["Address", "Sold Price", "Date Sold", "SqFt", "Beds", "Baths", "Dist (mi)", "Match Level", "Matched Schools"]
                
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
            # Display Execution Log
            st.divider()
            st.subheader("Execution Log")
            st.code(output_log, language="text")
