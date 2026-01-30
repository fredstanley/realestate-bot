# Real Estate Comps Finder & Flipper Bot

## Phase 1: Comp Analysis Workflow
- [x] Integrate Realie.ai API <!-- id: 5 -->
    - [x] Create `.env` & `requirements.txt`
    - [x] Fetch property coordinates & comps (`get_comps.py`)
    - [x] Implement caching for API calls
- [x] Implement Filtering Logic
    - [x] Filter by date (last 36 months)
    - [x] Filter by Zip Code (School proxy)
    - [x] Filter: Exclude non-residential properties
    - [x] Fix: SqFt Filter (+/- 500 sqft tolerance)
    - [x] Fix: Price Filter (Exclude < $500k)
    - [x] Fix: Include 'Intrafamily Transfer' & 'Quit Claim' doc types
- [x] Build Streamlit UI (Comps Finder) <!-- id: 4 -->
    - [x] Address Input & Radius Slider
    - [x] Display Comps Table (Sorted High-to-Low)
    - [x] Display Metrics & Execution Log
- [x] AI ARV Analysis (Gemini) <!-- id: 6 -->
    - [x] Create Realtor System Prompt
    - [x] Display Streaming ARV Report
- [x] RentCast Integration (Pending Listings)
    - [x] Switch to "Pending" data source
    - [x] Sort by "Closest SqFt Match"
    - [x] Create "Consolidated Market Data" view

## Phase 2: Flipper Analysis Workflow
- [x] Create Flipper Service
    - [x] Logic to fetch 4-year history
    - [x] Identify short-term flips (< 18 months initially)
- [x] Build Flipper Detector UI
    - [x] Add Flipper Tab to `app.py`
    - [x] **Address Search**: Implement **Triangular Grid Scan** (Max 4 Calls) to broadly cover 10-mile radius.
    - [x] **Caching**: Implemented `st.cache_data` for Flipper results to minimize API costs.
    - [x] UI Simplification: Remove Zip/Radius toggles (Address-Only)
- [x] Implement Advanced Flipper Logic (Verified Flips) <!-- id: 29 -->
    - [x] **Timeframe**: Hold time must be between **30 and 550 days** (approx 1-18 months).
    - [x] **Profit**: Sale Price must be at least **15% higher** than Buy Price (Relaxed).
    - [x] **Entity**: (Bonus) Buyers named **LLC, CORP, or INC** are flagged as "Corporate Flips". Personal flips are also included.
- [x] Verification
    - [x] Test with known flip addresses
    - [x] Verify Entity detection works
