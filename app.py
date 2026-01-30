import streamlit as st
import os
import pandas as pd
import io
import contextlib
from dotenv import load_dotenv
from get_comps import find_comps, parse_address_string, get_coordinates
from flipper_service import find_flips, find_flips_via_magic_search
from google import genai

load_dotenv()

@st.cache_data(show_spinner=False)
def get_comps_with_log(address, radius, api_key):
    # Capture stdout
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        comps, raw_comps, error = find_comps(address, radius, api_key)
    return comps, raw_comps, error, f.getvalue()

@st.cache_data(show_spinner=False)
def generate_arv_analysis(api_key, model_name, prompt):
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model_name,
        contents=prompt
    )
    return response.text

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
        
    # Gemini API Key
    default_gemini_key = os.getenv("GEMINI_API_KEY", "")
    gemini_key = st.sidebar.text_input("Gemini API Key", type="password", value=default_gemini_key)
    
    # Radius Slider
    st.divider()
    search_radius = st.sidebar.slider("Search Radius (Miles)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
    
    st.divider()
    app_mode = st.selectbox("Select Tool", ["Comps Finder", "Flipper Detector"])

if app_mode == "Flipper Detector":
    st.title("💸 High-Velocity Sales Detector")
    st.markdown("Find properties bought and sold within **90 - 550 days** (approx 3 - 18 months). Includes **Losses/Wholesale** deals.")
    
    addr_input = st.text_input("Enter Address", placeholder="e.g. 3043 Rosato Ct, San Jose, CA")
    
    @st.cache_data(show_spinner=False)
    def get_flips_magic_cached(zip_code, api_key):
        from flipper_service import find_flips_via_magic_search
        return find_flips_via_magic_search(zip_code, api_key, limit=100, days_back=550)

    if st.button("Scan for Velocity Deals", type="primary"):
        if not api_key_input:
            st.error("API Key missing.")
        elif not addr_input:
            st.error("Enter an Address.")
        else:
            parsed = parse_address_string(addr_input)
            if not parsed or not parsed.get('zip_code'):
                st.error("Invalid Address Format. Could not extract Zip Code.")
            else:
                target_zip = parsed['zip_code']
                st.info(f"Scanning Zip Code: {target_zip} (3-Page Deep Scan)...")
                
                with st.spinner(f"Scanning {target_zip} for rapid sales (90-550 Days)..."):
                    # Search (Cached)
                    flips, err = get_flips_magic_cached(target_zip, api_key_input)
                    
                    if err:
                        st.error(err)
                    elif not flips:
                        st.info(f"No high-velocity deals found in {target_zip} (90-550 days hold).")
                    else:
                        st.success(f"Found {len(flips)} Verified Flips in {target_zip}!")
                        
                        # Summary Metrics
                        avg_profit = sum([f['profit'] for f in flips]) / len(flips)
                        st.metric("Avg Gross Profit", f"${avg_profit:,.0f}")
                        st.divider()
                        
                        for f in flips:
                            with st.container():
                                st.subheader(f.get('address'))
                                c1, c2, c3, c4 = st.columns(4)
                                c1.metric("Profit", f"${f['profit']:,.0f}", f"{f['margin']}%")
                                c2.metric("Hold Time", f"{f['hold_months']} Mo")
                                c3.metric("Buy Price", f"${f['bought_price']:,}")
                                c4.metric("Sell Price", f"${f['sold_price']:,}")
                                
                                st.caption(f"Bought: {f['bought_date']} | Sold: {f['sold_date']}")
                                
                                # Display Flip Type
                                ftype = f.get('type')
                                fgrantee = f.get('flipper_name', 'Unknown')
                                if "Corporate" in ftype:
                                    st.markdown(f"**Type:** :office: `{ftype}` ({fgrantee})")
                                else:
                                    st.markdown(f"**Type:** :person: `{ftype}` ({fgrantee})")
                                
                                st.divider()
    st.stop()


# Main Input
address_input = st.text_input("Enter Property Address", placeholder="e.g. 2048 Mayfield Ave, San Jose, CA 95130", help="Format: Street, City, State Zip")

if st.button("Find Comps", type="primary"):
    if not api_key_input:
        st.error("API Key is missing!")
    elif not address_input:
        st.error("Please enter an address.")
    else:
        with st.spinner("Fetching comps..."):
            comps, raw_comps, error, output_log = get_comps_with_log(address_input, search_radius, api_key_input)
            
            if error:
                st.error(error)
            elif not comps:
                st.info("No comps found matching the criteria (1 Mile, 24 Months, Same Zip/School).")
                if raw_comps:
                    st.warning(f"However, {len(raw_comps)} raw comps were returned from the API. Check 'Raw API Response' below.")
            else:
                st.success(f"Found {len(comps)} comps! (Sorted by Price: High to Low)")
                
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


            # AI ARV Analysis
            st.divider()
            st.header("🤖 AI ARV Analysis")
            
            if not gemini_key:
                st.error("Please enter your Gemini API Key in the sidebar.")
            else:
                try:
                    # model name is hardcoded or could be passed? logic was:
                    model_name = 'gemini-3-pro-preview'
                    
                    # Prepare Context
                    subject_desc = f"{address_input} (Subject)" 
                    
                    # Parse subject zip for filtering raw comps
                    parsed_addr = parse_address_string(address_input)
                    subject_zip = parsed_addr.get('zip_code') if parsed_addr else None
                    
                    filtered_raw_string = "No raw data available."
                    if raw_comps:
                        # Filter raw comps by zip
                        if subject_zip:
                            # Ensure loose matching (str vs int)
                            zip_filtered = [c for c in raw_comps if str(c.get('zipCode', '')) == str(subject_zip)]
                        else:
                            zip_filtered = raw_comps
                            
                        if zip_filtered:
                             filtered_raw_string = pd.DataFrame(zip_filtered)[['address', 'transferPrice', 'transferDate', 'buildingArea', 'totalBedrooms', 'totalBathrooms']].rename(columns={'transferPrice':'price', 'buildingArea':'sqft', 'totalBedrooms':'beds', 'totalBathrooms':'baths', 'transferDate':'date'}).to_string(index=False)
                        else:
                             filtered_raw_string = f"No raw comps found in zip {subject_zip}."

                    prompt = f"""
                    You are a Senior Real Estate Appraiser with 20 years of experience in the California market.
                    
                    **Objective**: Determine the After Repair Value (ARV) for the Subject Property based on the provided comps.
                    
                    **Subject Property**: {subject_desc}
                    
                    **Verified Comparable Properties (Filtered - High Confidence)**:
                    {display_df.to_string(index=False)}

                    **Raw Market Data (Unfiltered - Same Zip Only)**:
                    The following are properties from the same zip code ({subject_zip}) returned by the search. Use these for broader market context.
                    {filtered_raw_string}
                    
                    **Task**:
                    1. Analyze the matched comps. Prioritize "3 Match" schools and recent sales.
                    2. Adjust for differences in square footage, bed/bath count, and date.
                    3. Provide a estimated ARV range and a recommended list price.
                    4. Explain your reasoning clearly.
                    """
                    
                    st.subheader("Fiz Real Estate Agent")
                    
                    with st.spinner("Generating ARV Analysis..."):
                        full_response = generate_arv_analysis(gemini_key, model_name, prompt)
                        st.markdown(full_response)
                    
                except Exception as e:
                    st.error(f"AI Analysis Failed: {e}")
                
            # Display Execution Log
            st.divider()
            
            with st.expander("Raw API Response (All Comps)", expanded=False):
                if raw_comps:
                    st.write(f"Total Raw Comps: {len(raw_comps)}")
                    raw_df = pd.DataFrame(raw_comps)
                    # Filter columns for readability if possible, or dump all? User said "dump all".
                    # Let's show specific useful columns first if they exist
                    cols = ['address', 'price', 'transferDate', 'buildingArea', 'bedrooms', 'bathroomsFull', 'bathsTotal', 'zipCode', 'transferDocType']
                    # Keep only columns that exist
                    valid_cols = [c for c in cols if c in raw_df.columns]
                    # If valid_cols found, put them first, but keep others? Or just dump.
                    # Let's just dump the dataframe, Streamlit handles searching/scrolling well.
                    st.dataframe(raw_df)
                else:
                    st.write("No raw comps data available.")

            st.subheader("Execution Log")
            st.code(output_log, language="text")
