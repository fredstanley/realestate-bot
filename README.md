# Real Estate Comps Bot

A Python-based tool to find real estate comparables using the Realie.ai API, with strict filtering for "Same School District" logic using the US Census Bureau API.

## Features
- **Strict School Matching**: Verifies comps are in the exact same Elementary/Secondary/Unified districts.
- **Granular Scoring**: "3 Match" (Unified/All), "2 Match" (Elem+Mid), "1 Match" (High).
- **Market Sale Filter**: Excludes non-arm's length transactions (e.g. Intrafamily transfers).
- **Interactive UI**: Streamlit dashboard.

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **API Key**:
   Ensure you have your Realie.ai API Key.

## Running the App

Run the Streamlit app using the python module syntax to ensure the correct environment is used:

```bash
# Replace with your actual API Key
REALIE_API_KEY=your_key_here .venv/bin/python -m streamlit run app.py
```

## Usage
1. Enter the full address (e.g. `2048 Mayfield Ave, San Jose, CA 95130`).
2. Click "Find Comps".
3. View the sorted list of comps, prioritized by School Match Score.
