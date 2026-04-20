import yfinance as yf
import pandas as pd
import requests_cache
from datetime import datetime, timedelta
import streamlit as st

# Cache TTL: 1 hour — applies to both the HTTP cache and st.cache_data
CACHE_TTL = 3600

# Persist yfinance HTTP responses to disk so app restarts don't re-fetch.
# requests_cache intercepts the underlying requests calls yfinance makes,
# stores raw responses in a local SQLite file, and replays them on restart
# if they're younger than CACHE_TTL. Without this, st.cache_data only
# survives while the process is alive.
requests_cache.install_cache("yfinance_cache", expire_after=CACHE_TTL)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_history(tickers: tuple, period: str = "2y") -> dict[str, pd.DataFrame]:
    """Download OHLCV history for a list of tickers."""
    raw = yf.download(
        list(tickers),
        period=period,
        auto_adjust=True,
        progress=False,
        group_by="ticker",
        threads=True,
    )
    result = {}
    if len(tickers) == 1:
        ticker = tickers[0]
        if not raw.empty:
            result[ticker] = raw[["Close", "Volume"]].copy()
    else:
        for ticker in tickers:
            try:
                df = raw[ticker][["Close", "Volume"]].dropna()
                if not df.empty:
                    result[ticker] = df
            except KeyError:
                pass
    return result


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def fetch_info(tickers: tuple) -> dict[str, dict]:
    """Fetch fundamental info (market cap, P/S, etc.) for each ticker."""
    info_map = {}
    for ticker in tickers:
        try:
            t = yf.Ticker(ticker)
            info = t.info

            # Next earnings date — yfinance calendar format varies by version
            earnings_date = None
            try:
                cal = t.calendar
                if isinstance(cal, pd.DataFrame) and not cal.empty:
                    # Columns are Timestamps in newer yfinance
                    dates = [c for c in cal.columns if hasattr(c, "date")]
                    if dates:
                        earnings_date = str(dates[0].date())
                elif isinstance(cal, dict):
                    ed = cal.get("Earnings Date") or cal.get("earningsDate")
                    if ed:
                        d = ed[0] if isinstance(ed, list) else ed
                        earnings_date = str(d.date()) if hasattr(d, "date") else str(d)[:10]
            except Exception:
                pass

            info_map[ticker] = {
                "market_cap":    info.get("marketCap"),
                "ps_ratio":      info.get("priceToSalesTrailing12Months"),
                "trailing_pe":   info.get("trailingPE"),
                "forward_pe":    info.get("forwardPE"),
                "company_name":  info.get("shortName", ticker),
                "website":       info.get("website", ""),
                "logo_url":      info.get("logo_url", ""),
                "earnings_date": earnings_date,
            }
        except Exception:
            info_map[ticker] = {}
    return info_map


def get_logo_url(ticker: str, logo_url: str = "", website: str = "") -> str:
    """Return best available logo URL. Priority: Yahoo Finance > Clearbit > fallback."""
    if logo_url:
        return logo_url
    if website:
        domain = website.replace("https://", "").replace("http://", "").split("/")[0]
        return f"https://logo.clearbit.com/{domain}"
    return ""


def format_market_cap(val) -> str:
    if val is None:
        return "n/a"
    if val >= 1e12:
        return f"${val/1e12:.1f}T"
    if val >= 1e9:
        return f"${val/1e9:.1f}B"
    if val >= 1e6:
        return f"${val/1e6:.0f}M"
    return f"${val:,.0f}"
