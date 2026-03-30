# Leading Stocks Dashboard

A real-time stock screening dashboard inspired by leading stock trackers, built with Python and Streamlit. Data is sourced entirely from Yahoo Finance — no API keys required.

![Dashboard Preview](26-01-13\ 18-58-23\ 3740.jpg)

## What it does

- Displays a curated universe of high-momentum stocks grouped by theme (Nuclear, Space, Drones, Semis, etc.)
- Shows key metrics: price, market cap, P/S ratio, % YTD / 1Y / 1M returns, 52-week high
- Calculates **Relative Strength (RS) Rank** using IBD-style recency-weighted 12-month performance
- Renders inline **SVG sparklines** for each stock (lightweight, no CDN dependency)
- Colour-coded **20 / 50 / 200-day SMA** indicators
- Sidebar filters: theme, minimum RS rank, sort column

## Stack

| Layer | Tool |
|---|---|
| Language | Python 3.12 |
| UI | Streamlit |
| Data | yfinance (Yahoo Finance) |
| Data processing | pandas, numpy |
| Package manager | uv |
| Version control | git |

## Setup

**Prerequisites:** Python 3.12+, [uv](https://github.com/astral-sh/uv) installed

```bash
# 1. Clone the repo
git clone <repo-url>
cd dashboard_260320

# 2. Create virtual environment and install dependencies
uv venv --python 3.12
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # Mac/Linux

uv sync

# 3. Run
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

## Project structure

```
dashboard_260320/
├── app.py          # Streamlit UI — layout, filters, table rendering
├── data.py         # yfinance data fetching with 1-hour cache
├── metrics.py      # RS rank, SMAs, returns, sparkline data
├── tickers.py      # Stock universe and theme/colour mapping
├── pyproject.toml  # Project metadata and dependencies (uv-native)
└── uv.lock         # Pinned dependency versions for reproducible installs
```

## Key technical decisions

- **SVG sparklines** instead of Plotly — avoids loading a JS CDN per table row, making the table render instantly
- **`st.cache_data` with 1-hour TTL** — prevents redundant Yahoo Finance requests on re-renders
- **RS Rank algorithm** mirrors IBD methodology: `0.4 × Q4 + 0.2 × Q3 + 0.2 × Q2 + 0.2 × Q1` performance, ranked as a percentile (1–99) against the full universe
- **`uv sync`** over `pip install -r requirements.txt` — reproducible installs from lockfile, ~10× faster

## Data sources

| Data | Source |
|---|---|
| Price, OHLCV history | Yahoo Finance via `yfinance` |
| Market cap, P/S ratio | Yahoo Finance `Ticker.info` |
| Company logos | Yahoo Finance `logo_url` → Clearbit fallback |
| RS Rank universe | Internal (our stocks + S&P 500 subset) |

## Adding stocks

Edit `tickers.py`:

```python
STOCKS = [
    {"ticker": "NVDA", "company": "NVIDIA", "theme": "Semis"},
    # add more here ...
]
```

Add a colour for any new theme in `THEME_COLORS`.

## License

MIT
