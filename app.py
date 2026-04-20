import html as html_lib
from datetime import date, datetime

import pandas as pd
import streamlit as st

import history_store
from data import fetch_history, fetch_info, format_market_cap, get_logo_url
from metrics import build_row, rs_rank_all
from tickers import STOCKS, THEME_COLORS, RS_UNIVERSE

st.set_page_config(
    page_title="Leading Stocks Dashboard",
    page_icon="📈",
    layout="wide",
)

st.markdown("""
<style>
    .main .block-container { padding-top: 1rem; padding-bottom: 0.5rem; }
    h1 { font-size: 1.8rem; font-weight: 800; margin-bottom: 0; }

    /* ── Table ── */
    .stock-table {
        border-collapse: collapse;
        width: 100%;
        font-size: 11px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .stock-table th {
        padding: 5px 8px;
        text-align: left;
        color: #666;
        border-bottom: 2px solid #2a2a2a;
        white-space: nowrap;
        font-weight: 600;
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .stock-table td {
        padding: 3px 8px;
        border-bottom: 1px solid #1a1a1a;
        vertical-align: middle;
        white-space: nowrap;
    }
    .stock-table tbody tr:hover td { background: #161625; }

    /* ── Badges ── */
    .badge {
        display: inline-block;
        padding: 1px 6px;
        border-radius: 3px;
        font-size: 9.5px;
        font-weight: 600;
        white-space: nowrap;
    }

    /* ── Numbers ── */
    .pos { color: #00e676; font-weight: 700; }
    .neg { color: #ff5252; font-weight: 700; }
    .na  { color: #444; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
today_str = datetime.today().strftime("%B %d, %Y")
st.markdown(f"# Leading Stocks {datetime.today().year}")
st.caption(f"Data via Yahoo Finance · Updated {today_str}")

# ── Filters — flat row of widgets (no expander, avoids JS module conflicts) ────
all_themes = sorted({s["theme"] for s in STOCKS})
fc1, fc2, fc3, fc4, fc5 = st.columns([4, 1.5, 2, 1, 1.2])
selected_themes = fc1.multiselect("Theme", all_themes, default=all_themes)
min_rs    = fc2.slider("Min RS", 0, 99, 0)
sort_col  = fc3.selectbox(
    "Sort by",
    ["% YTD", "% 1Y", "% 3M", "% 1M", "% 1D", "RS Rank", "Market Cap", "Vol"],
)
sort_asc  = fc4.checkbox("Ascending", value=False)

# ── Data ───────────────────────────────────────────────────────────────────────
tickers_main = tuple(s["ticker"] for s in STOCKS)
tickers_all  = tuple(set(list(tickers_main) + RS_UNIVERSE))

with st.spinner("Fetching market data…"):
    history_all  = fetch_history(tickers_all, period="2y")
    history_main = {t: history_all[t] for t in tickers_main if t in history_all}
    close_all    = {t: df["Close"] for t, df in history_all.items()}
    close_main   = {t: df["Close"] for t, df in history_main.items()}
    info_map     = fetch_info(tickers_main)

# ── RS Ranks — compute once for the whole universe, then persist ───────────────
rs_ranks = rs_rank_all(close_all)
history_store.save_snapshot({t: rs_ranks[t] for t in tickers_main if rs_ranks.get(t)})
rs_prev = history_store.load_prev_snapshot(days_back=5)

# ── Build rows ─────────────────────────────────────────────────────────────────
rows = [
    build_row(
        s["ticker"], s, close_main, info_map, close_all,
        df_main=history_main,
        rs_rank_val=rs_ranks.get(s["ticker"]),
        rs_rank_prev=rs_prev.get(s["ticker"]),
    )
    for s in STOCKS
]
df = pd.DataFrame(rows)

# ── Filter + sort ──────────────────────────────────────────────────────────────
df = df[df["theme"].isin(selected_themes)]
if min_rs > 0:
    df = df[df["rs_rank"].fillna(0) >= min_rs]

sort_map = {
    "% YTD":      "pct_ytd",
    "% 1Y":       "pct_1y",
    "% 3M":       "pct_3m",
    "% 1M":       "pct_1m",
    "% 1D":       "pct_1d",
    "RS Rank":    "rs_rank",
    "Market Cap": "market_cap",
    "Vol":        "vol_ratio",
}
df = (df
      .sort_values(sort_map[sort_col], ascending=sort_asc, na_position="last")
      .reset_index(drop=True))

# ── CSV export ─────────────────────────────────────────────────────────────────
export_cols = {
    "ticker": "Ticker", "company": "Company", "theme": "Theme",
    "price": "Price", "pct_1d": "% 1D", "market_cap": "Market Cap",
    "ps_ratio": "P/S", "trailing_pe": "P/E", "forward_pe": "Fwd P/E",
    "pct_ytd": "% YTD", "pct_3m": "% 3M", "pct_1y": "% 1Y", "pct_1m": "% 1M",
    "pct_from_52h": "% from High", "rs_rank": "RS Rank", "rs_delta": "RS Δ",
    "vol_ratio": "Vol Ratio", "earnings_date": "Earnings Date",
}
csv_df = df[[c for c in export_cols if c in df.columns]].rename(columns=export_cols)
fc5.download_button(
    "⬇ Export CSV",
    csv_df.to_csv(index=False),
    file_name=f"leading_stocks_{date.today()}.csv",
    mime="text/csv",
)


# ── SVG helpers ────────────────────────────────────────────────────────────────

def sparkline_svg(data: list, w: int = 64, h: int = 28) -> str:
    """Inline SVG sparkline — 1-year price history, area fill."""
    if not data or len(data) < 2:
        return ""
    color = "#00e676" if data[-1] >= data[0] else "#ff5252"
    mn, mx = min(data), max(data)
    rng = mx - mn or 1
    pad = 2
    xs = [round(i / (len(data) - 1) * w, 1) for i in range(len(data))]
    ys = [round(h - pad - (v - mn) / rng * (h - pad * 2), 1) for v in data]
    pts  = " ".join(f"{x},{y}" for x, y in zip(xs, ys))
    fill = f"0,{h} " + pts + f" {w},{h}"
    return (
        f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg" style="display:block">'
        f'<polygon points="{fill}" fill="{color}" fill-opacity="0.12"/>'
        f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="1.3" stroke-linejoin="round"/>'
        f'</svg>'
    )


def rs_spy_sparkline_svg(cum_data: list, w: int = 72, h: int = 28) -> str:
    """
    Cumulative RS vs SPY sparkline over ~20 trading days (1 month).
    Plots the running outperformance directly — a rising line means the stock
    is pulling away from SPY; falling means it's fading. The dashed baseline
    at y=0 makes the total 1-month delta readable at a glance.
    """
    if not cum_data or len(cum_data) < 2:
        return '<span class="na">—</span>'

    final = cum_data[-1]
    color = "#00e676" if final >= 0 else "#ff5252"

    # Include 0 in the range so the baseline is always visible
    mn  = min(min(cum_data), 0)
    mx  = max(max(cum_data), 0)
    rng = mx - mn or 1
    pad = 3

    def _y(v: float) -> float:
        return round(h - pad - (v - mn) / rng * (h - pad * 2), 1)

    n   = len(cum_data)
    xs  = [round(i / (n - 1) * w, 1) for i in range(n)]
    ys  = [_y(v) for v in cum_data]
    pts = " ".join(f"{x},{y}" for x, y in zip(xs, ys))

    zero_y    = _y(0)
    fill_pts  = f"0,{zero_y} " + pts + f" {w},{zero_y}"

    return (
        f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg" style="display:block">'
        f'<line x1="0" y1="{zero_y}" x2="{w}" y2="{zero_y}" '
        f'stroke="#555" stroke-width="0.8" stroke-dasharray="2,2"/>'
        f'<polygon points="{fill_pts}" fill="{color}" fill-opacity="0.15"/>'
        f'<polyline points="{pts}" fill="none" stroke="{color}" '
        f'stroke-width="1.4" stroke-linejoin="round"/>'
        f'</svg>'
    )


# ── Cell renderers ─────────────────────────────────────────────────────────────

def color_pct(val) -> str:
    if val is None:
        return '<span class="na">n/a</span>'
    cls  = "pos" if val >= 0 else "neg"
    sign = "+" if val > 0 else ""
    return f'<span class="{cls}">{sign}{val:.1f}%</span>'


def fmt_num(val, decimals: int = 1) -> str:
    if val is None or (isinstance(val, float) and val != val):
        return '<span class="na">n/a</span>'
    return f"{val:.{decimals}f}"


def theme_badge(theme: str) -> str:
    color = THEME_COLORS.get(theme, "#555")
    return (
        f'<span class="badge" '
        f'style="background:{color}22;color:{color};border:1px solid {color}44">'
        f'{html_lib.escape(theme)}</span>'
    )


def sma_dots(a20: bool, a50: bool, a200: bool) -> str:
    def dot(on: bool) -> str:
        return ('<span style="color:#00e676">●</span>' if on
                else '<span style="color:#333">●</span>')
    return f'{dot(a20)}&thinsp;{dot(a50)}&thinsp;{dot(a200)}'


def rs_cell(rs) -> str:
    if not rs:
        return '<span class="na">—</span>'
    color = "#00e676" if rs >= 80 else ("#ffeb3b" if rs >= 50 else "#ff5252")
    return f'<b style="color:{color}">{rs}</b>'


def rs_delta_cell(delta: int | None) -> str:
    """RS Rank change vs snapshot from ~5 days ago. — when no prior data."""
    if delta is None:
        return '<span class="na">—</span>'
    if delta > 0:
        return f'<span style="color:#00e676;font-size:10px">↑+{delta}</span>'
    if delta < 0:
        return f'<span style="color:#ff5252;font-size:10px">↓{delta}</span>'
    return '<span style="color:#555;font-size:10px">—</span>'


def vol_ratio_cell(ratio: float | None) -> str:
    """Volume vs 50-day average. Colour-coded by magnitude."""
    if ratio is None:
        return '<span class="na">—</span>'
    if ratio >= 2.0:
        color = "#00e676"
    elif ratio >= 1.5:
        color = "#b2ff59"
    elif ratio >= 0.8:
        color = "#888"
    else:
        color = "#555"
    return f'<span style="color:{color}">{ratio:.1f}×</span>'


def earnings_cell(date_str: str | None) -> str:
    """Days until next earnings. Yellow warning if ≤14 days away."""
    if not date_str:
        return '<span class="na">—</span>'
    try:
        ed   = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
        days = (ed - date.today()).days
        if days < 0:
            return '<span class="na">—</span>'
        elif days <= 14:
            return f'<b style="color:#ffeb3b">{days}d</b>'
        else:
            return f'<span style="color:#666">{days}d</span>'
    except Exception:
        return '<span class="na">—</span>'


# ── Build HTML table ───────────────────────────────────────────────────────────
HEADERS = [
    "#", "Logo", "Ticker / Company", "Theme",
    "Price", "% 1D", "Mkt Cap", "P/S", "P/E", "Fwd P/E",
    "Sparkline", "% YTD", "% 3M", "% 1Y", "% 1M", "% from High",
    "RS", "RS Δ", "SMA 20·50·200", "Vol", "RS vs SPY (1M)", "Earnings",
]

header_html = "".join(f"<th>{h}</th>" for h in HEADERS)

row_htmls = []
for i, row in df.iterrows():
    logo_url = get_logo_url(row["ticker"], row.get("logo_url", ""), row.get("website", ""))

    fpe     = row.get("forward_pe")
    fpe_str = f"{fpe:.1f}" if fpe and fpe > 0 else '<span class="na">n/a</span>'

    price_str = (f"${row['price']:.2f}" if row.get("price")
                 else '<span class="na">n/a</span>')

    tds = [
        f'<td style="color:#555;font-size:10px">{i + 1}</td>',
        (f'<td><img src="{logo_url}" width="20" height="20" '
         f'style="border-radius:3px;object-fit:contain;vertical-align:middle" '
         f'onerror="this.style.display=\'none\'"></td>'),
        (f'<td>'
         f'<b style="font-size:11.5px">{html_lib.escape(row["ticker"])}</b>'
         f'<br><span style="font-size:9.5px;color:#666">{html_lib.escape(row["company"])}</span>'
         f'</td>'),
        f'<td>{theme_badge(row["theme"])}</td>',
        f'<td>{price_str}</td>',
        f'<td>{color_pct(row.get("pct_1d"))}</td>',
        f'<td>{format_market_cap(row["market_cap"])}</td>',
        f'<td>{fmt_num(row.get("ps_ratio"))}</td>',
        f'<td>{fmt_num(row.get("trailing_pe"))}</td>',
        f'<td>{fpe_str}</td>',
        f'<td style="padding:2px 6px">{sparkline_svg(row["sparkline"])}</td>',
        f'<td>{color_pct(row["pct_ytd"])}</td>',
        f'<td>{color_pct(row.get("pct_3m"))}</td>',
        f'<td>{color_pct(row["pct_1y"])}</td>',
        f'<td>{color_pct(row["pct_1m"])}</td>',
        f'<td>{color_pct(row.get("pct_from_52h"))}</td>',
        f'<td>{rs_cell(row["rs_rank"])}</td>',
        f'<td>{rs_delta_cell(row.get("rs_delta"))}</td>',
        f'<td>{sma_dots(row["above_20"], row["above_50"], row["above_200"])}</td>',
        f'<td>{vol_ratio_cell(row.get("vol_ratio"))}</td>',
        f'<td style="padding:2px 6px">{rs_spy_sparkline_svg(row.get("rs_spy_cum", []))}</td>',
        f'<td>{earnings_cell(row.get("earnings_date"))}</td>',
    ]
    row_htmls.append(f'<tr>{"".join(tds)}</tr>')

table_html = f"""
<div style="overflow-x:auto; width:100%; margin-top:0.5rem">
  <table class="stock-table">
    <thead><tr>{header_html}</tr></thead>
    <tbody>{"".join(row_htmls)}</tbody>
  </table>
</div>
"""

st.markdown(table_html, unsafe_allow_html=True)
st.caption(
    "Source: Yahoo Finance via yfinance · RS Rank calculated vs internal universe · "
    "RS Δ vs snapshot ~5 days ago · Logos via Clearbit / Yahoo Finance"
)
