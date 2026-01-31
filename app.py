import streamlit as st
import os
import pandas as pd
import io
import contextlib
from dotenv import load_dotenv
from get_comps import find_comps, parse_address_string
from google import genai
from email_utils import send_email_with_pdf
import requests
from streamlit_searchbox import st_searchbox


load_dotenv()

@st.cache_data(show_spinner=False)
def get_comps_with_log(address, radius, api_key, gemini_key, known_coords=None):
    # Capture stdout
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        comps, raw_comps, error = find_comps(address, radius, api_key, gemini_key, known_coords)
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

# Placeholder for Download Button
download_placeholder = st.empty()

# Sidebar for API Key
with st.sidebar:
    st.header("Settings")
    # Realie API Key
    env_realie_key = os.getenv("REALIE_API_KEY")
    if env_realie_key:
        api_key_input = env_realie_key
        st.success("✅ Realie API Key loaded")
    else:
        api_key_input = st.text_input("Realie API Key", type="password")
        if not api_key_input:
            st.warning("Please enter your API Key to proceed.")
        
    # Gemini API Key
    env_gemini_key = os.getenv("GEMINI_API_KEY")
    if env_gemini_key:
        gemini_key = env_gemini_key
        st.success("✅ Gemini API Key loaded")
    else:
        gemini_key = st.text_input("Gemini API Key", type="password")
    
    # Radius Slider
    st.divider()
    search_radius = st.sidebar.slider("Search Radius (Miles)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)


import json

# Main Input
# Define Nominatim Search Function
def search_nominatim(searchterm: str):
    if not searchterm: 
        return []
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": searchterm,
        "format": "json",
        "countrycodes": "us",
        "limit": 5,
        "addressdetails": 1
    }
    headers = {'User-Agent': 'RealEstateCompsBot/1.0'}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Return list of tuples: (display_label, value_json_string)
            # Serialize dict to string to avoid widget state issues
            return [(d['display_name'], json.dumps(d)) for d in data]
        else:
            return []
    except Exception:
        return []

st.markdown("### Property Search")
selected_input = st_searchbox(
    search_nominatim, 
    key="address_autocomplete",
    placeholder="Start typing address (e.g. 2048 Mayfield)...",
)

# Restore Email Input
recipient_email = st.text_input("Email Report To (Optional)", placeholder="client@example.com", help="If provided, the report will be auto-emailed here.")

# Handle Input Type
address_string = ""
known_coords = None

if selected_input:
    # Try to parse as JSON (new behavior)
    try:
        # It's a string, try to decode
        input_data = json.loads(selected_input)
        if isinstance(input_data, dict):
            # User selected from dropdown
            address_string = input_data.get('display_name', '')
            try:
                lat = float(input_data.get('lat'))
                lon = float(input_data.get('lon'))
                known_coords = (lat, lon)
                st.success(f"📍 Location identified: {address_string[:50]}...")
            except:
                pass
        else:
            # Should not happen if logic holds, but fallback
            address_string = str(selected_input)
    except json.JSONDecodeError:
        # User typed raw text (not a JSON string from dropdown)
        address_string = str(selected_input)

# Fallback text input if they want to override or didn't use searchbox? 
# st_searchbox handles typing.

if st.button("Find Comps", type="primary"):
    if not api_key_input:
        st.error("API Key is missing!")
    elif not address_string:
        st.error("Please select or enter an address.")
    else:
        with st.spinner("Resolving address & Fetching comps..."):
            comps, raw_comps, error, output_log = get_comps_with_log(address_string, search_radius, api_key_input, gemini_key, known_coords)
            
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
                    subject_desc = f"{address_string} (Subject)" 
                    
                    # Parse subject zip for filtering raw comps
                    parsed_addr = parse_address_string(address_string)
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

                # PDF Generation
                if 'full_response' in locals():
                    from pdf_report import generate_pdf
                    
                    # Generate PDF
                    pdf_bytes = generate_pdf(full_response, comps, address_string)
                    
                    st.download_button(
                        label="📄 Download ARV Report (PDF)",
                        data=pdf_bytes,
                        file_name=f"ARV_Report_{address_string.replace(' ', '_').replace(',', '')}.pdf",
                        mime="application/pdf"
                    )
                    
                    # Also show at the top
                    download_placeholder.download_button(
                        label="📄 Download ARV Report (PDF) - Top",
                        data=pdf_bytes,
                        file_name=f"ARV_Report_{address_string.replace(' ', '_').replace(',', '')}.pdf",
                        mime="application/pdf",
                        key="download_top"
                    )

                    # Email Sending Button
                    # Auto-Email Logic
                    # Auto-Email Logic
                    if recipient_email:
                        st.divider()
                        env_sender = os.getenv("SENDER_EMAIL")
                        env_app_pass = os.getenv("APP_PASSWORD")

                        if not env_sender or not env_app_pass:
                           st.warning("⚠️ Email provided, but SENDER credentials are missing in .env. Cannot auto-send.")
                        else:
                            with st.spinner(f"Auto-sending report to {recipient_email}..."):
                                success, msg = send_email_with_pdf(pdf_bytes, recipient_email, env_sender, env_app_pass, address_string)
                                if success:
                                    st.success(f"✅ Email sent successfully to {recipient_email}!")
                                else:
                                    st.error(f"❌ Failed to send email: {msg}")
                
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
