# Leading Stocks Dashboard

A real-time stock screening dashboard inspired by leading stock trackers, built with Python and Streamlit. Data is sourced entirely from Yahoo Finance — no API keys required.



## What it does

- Displays a curated universe of high-momentum stocks grouped by theme (Nuclear, Space, Drones, Semis, etc.)
- Shows key metrics: price, % 1D / 1M / 3M / 1Y / YTD returns, % from 52-week high, market cap, P/S, P/E, Fwd P/E
- Calculates **Relative Strength (RS) Rank** using IBD-style recency-weighted 12-month performance
- Tracks **RS Rank trend (RS Δ)** — compares today's rank against a snapshot from ~5 days ago to show momentum direction
- Renders inline **SVG sparklines** (1-year price history) and **RS vs SPY bar charts** (20-day relative performance)
- **Volume ratio** — today's volume vs 50-day average, colour-coded to flag breakouts
- **Earnings countdown** — days until next earnings date, highlighted in yellow when ≤14 days away
- **CSV export** — one-click download of the filtered, sorted table
- Colour-coded **20 / 50 / 200-day SMA** indicators
- Filters: theme multi-select, minimum RS rank, sort column (including Vol and % 1D)

## Stack

| Layer | Tool |
|---|---|
| Language | Python 3.12 |
| UI | Streamlit |
| Data | yfinance (Yahoo Finance) |
| Data processing | pandas, numpy |
| RS history | SQLite (local, via `history_store.py`) |
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
streamlit run app.py # Or skip activation entirely and just use:

cd \path_to_folder
uv run streamlit run app.py     # uv always uses the project's own .venv
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

On first load, RS Δ will show `—` for all rows — the SQLite snapshot needs at least one prior day to compute a delta.

## Project structure

```
dashboard_260320/
├── app.py              # Streamlit UI — layout, filters, table rendering, SVG helpers
├── data.py             # yfinance data fetching with 1-hour cache
├── metrics.py          # RS rank, SMAs, returns, volume ratio, sparkline data
├── tickers.py          # Stock universe and theme/colour mapping
├── history_store.py    # SQLite persistence for daily RS rank snapshots (RS Δ trend)
├── pyproject.toml      # Project metadata and dependencies (uv-native)
└── uv.lock             # Pinned dependency versions for reproducible installs
```

`rs_history.db` is created automatically on first run and gitignored.

## Key technical decisions

- **SVG sparklines** instead of Plotly — avoids loading a JS CDN per table row; table renders instantly
- **`st.cache_data` with 1-hour TTL** — prevents redundant Yahoo Finance requests on every re-render
- **RS Rank computed once for the whole universe** (`rs_rank_all`) — O(n) single pass vs the naïve O(n²) per-ticker approach
- **RS Rank methodology** mirrors IBD: `0.4 × Q4 + 0.2 × Q3 + 0.2 × Q2 + 0.2 × Q1`, ranked as percentile (1–99) against the full universe
- **SQLite for RS history** — appends ~80 rows/day; trivially small, zero infrastructure, single writer
- **`uv sync`** over `pip install -r requirements.txt` — reproducible installs from lockfile, ~10× faster

## Data sources

| Data | Source |
|---|---|
| Price, OHLCV history | Yahoo Finance via `yfinance` |
| Market cap, P/S, P/E | Yahoo Finance `Ticker.info` |
| Earnings date | Yahoo Finance `Ticker.calendar` |
| Company logos | Yahoo Finance `logo_url` → Clearbit fallback |
| RS Rank universe | Internal (our stocks + S&P 500 subset + SPY/QQQ/IWM) |

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
