# Real Estate Comps Finder & ARV Agent

A powerful AI-driven tool to find real estate comparables and calculate After Repair Value (ARV) using Realie.ai data and Google Gemini AI.

## Features

### 🔍 Smart Filtering
- **3-Year Search Window**: Finds comps sold in the last 36 months.
- **Configurable Radius**: Adjust search radius (0.1 - 5 miles) via sidebar slider.
- **Intrafamily Transfers (IT) Included**: Captures **Off-Market** sales that appear as transfers.
- **Anomaly Detection**:
    - **Minimum Price Filter**: Excludes transfers < $500k (removes "paperwork" transfers).
    - **Outlier Filter**: Removes properties that deviate > $500k from the median price (if 3+ comps exist).
- **Zip Code Context**: Filters raw market data by the subject's zip code for the AI.

### 🤖 AI Analysis
- **Automated ARV**: Automatically generates an "Appraiser-Level" analysis using Google Gemini.
- **Context-Aware**: Feeds both "Verified Comps" and "Raw Market Data" to the AI for accurate valuation.

### ⚡ Performance
- **Caching**: Caches API calls and AI responses to start instant-loading on repeat searches.
- **Robustness**: Handles missing data and API errors gracefully.

---

## 🚀 Setup & Installation

### 1. Clone & Install
```bash
pip install -r requirements.txt
```

### 2. API Keys
You need two API keys:
1.  **Realie.ai API Key** (for data)
2.  **Google Gemini API Key** (for AI analysis)

#### Local Development
Create a `.env` file in the root directory:
```bash
REALIE_API_KEY="your_realie_key"
GEMINI_API_KEY="your_gemini_key"
```
*Note: The app will auto-load these keys.*

#### Streamlit Cloud Deployment
**DO NOT commit your `.env` file.**
1.  Deploy your app.
2.  Go to **App Settings** -> **Secrets**.
3.  Add your keys in TOML format:

```toml
REALIE_API_KEY = "your_realie_key"
GEMINI_API_KEY = "your_gemini_key"
```

---

## 🖥️ Usage

1.  **Run the App**:
    ```bash
    streamlit run app.py
    ```
2.  **Enter Address**: Type the full address (e.g., `3043 Rosato Ct, San Jose, CA 95135`).
3.  **Adjust Radius**: Use the sidebar slider if needed.
4.  **Find Comps**: Click the button.
5.  **View Results**:
    - **Top Comps Table**: The best matches.
    - **AI Analysis**: Scroll down for the "Fiz Real Estate Agent" report.
    - **Logs**: Expand "Execution Log" or "Raw API Response" for debugging.

---

## 🛠️ Troubleshooting
- **Missing Google API Key Box?**
    - If you set `GEMINI_API_KEY` in your `.env` or Streamlit Secrets, the box in the sidebar will be pre-filled with password dots (`••••••`). This is normal! You don't need to re-enter it.
- **No Comps Found?**
    - Try increasing the **Search Radius** slider.
    - Check the "Raw API Response" to see if the property exists but was filtered out (e.g. valid date but low price?).
