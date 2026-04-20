import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def pct_return(close: pd.Series, days: int) -> float | None:
    """Return % change over the last `days` trading days."""
    if close is None or len(close) < 2:
        return None
    end = close.iloc[-1]
    start_idx = max(0, len(close) - days - 1)
    start = close.iloc[start_idx]
    if start == 0:
        return None
    return round((end - start) / start * 100, 2)


def ytd_return(close: pd.Series) -> float | None:
    """Return % change from Jan 1 of current year to latest close."""
    if close is None or close.empty:
        return None
    year_start = datetime(datetime.today().year, 1, 1)
    ytd_data = close[close.index >= pd.Timestamp(year_start)]
    if ytd_data.empty or len(ytd_data) < 2:
        return None
    return round((ytd_data.iloc[-1] - ytd_data.iloc[0]) / ytd_data.iloc[0] * 100, 2)


def sma(close: pd.Series, window: int) -> float | None:
    """Latest simple moving average value."""
    if close is None or len(close) < window:
        return None
    return round(close.rolling(window).mean().iloc[-1], 2)


def high_52w(close: pd.Series) -> float | None:
    """52-week high."""
    if close is None or close.empty:
        return None
    one_year_ago = pd.Timestamp(datetime.today() - timedelta(days=365))
    recent = close[close.index >= one_year_ago]
    if recent.empty:
        return None
    return round(recent.max(), 2)


def pct_from_high(close: pd.Series) -> float | None:
    """% below the 52-week high (0 = at high, negative = below)."""
    h = high_52w(close)
    if h is None or close is None or close.empty:
        return None
    current = close.iloc[-1]
    return round((current - h) / h * 100, 2)


def volume_ratio(df: pd.DataFrame, window: int = 50) -> float | None:
    """
    Today's volume divided by the N-day average volume.
    >1.5 = elevated, >2.0 = surge. Useful for spotting breakouts.
    """
    if df is None or "Volume" not in df.columns or len(df) < window + 1:
        return None
    avg = df["Volume"].iloc[-(window + 1):-1].mean()
    today_vol = df["Volume"].iloc[-1]
    if avg == 0 or pd.isna(avg):
        return None
    return round(float(today_vol) / float(avg), 1)


def rs_rank_all(history: dict[str, pd.Series]) -> dict[str, int | None]:
    """
    Compute RS Rank (1–99) for ALL tickers in a single pass — O(n) not O(n²).
    IBD-style 12-month score with recency weighting:
        score = 0.4×Q4 + 0.2×Q3 + 0.2×Q2 + 0.2×Q1
    """
    def _score(close: pd.Series) -> float | None:
        if close is None or len(close) < 50:
            return None
        n = len(close)
        q4 = (close.iloc[-1] / close.iloc[max(0, n - 63)] - 1)       if n >= 63  else None
        q3 = (close.iloc[max(0, n - 63)]  / close.iloc[max(0, n - 126)] - 1) if n >= 126 else None
        q2 = (close.iloc[max(0, n - 126)] / close.iloc[max(0, n - 189)] - 1) if n >= 189 else None
        q1 = (close.iloc[max(0, n - 189)] / close.iloc[max(0, n - 252)] - 1) if n >= 252 else None
        parts = [(q4, 0.4), (q3, 0.2), (q2, 0.2), (q1, 0.2)]
        total_w = sum(w for v, w in parts if v is not None)
        if total_w == 0:
            return None
        return sum(v * w for v, w in parts if v is not None) / total_w

    scores = {t: _score(h) for t, h in history.items() if h is not None}
    valid  = {t: s for t, s in scores.items() if s is not None}
    if len(valid) < 2:
        return {t: None for t in history}

    all_scores = sorted(valid.values())
    result: dict[str, int | None] = {}
    for t in history:
        s = valid.get(t)
        if s is None:
            result[t] = None
        else:
            rank_pct = np.searchsorted(all_scores, s, side="left") / len(all_scores)
            result[t] = max(1, min(99, int(rank_pct * 99) + 1))
    return result


def rs_spy_cumulative(close: pd.Series, spy_close: pd.Series, days: int = 20) -> list[float]:
    """
    Cumulative daily RS vs SPY over the last `days` trading days (~1 month).
    Returns cumulative outperformance in percentage points starting near 0.
    A rising line = stock accelerating vs SPY; falling = fading.
    """
    if close is None or spy_close is None:
        return []
    aligned = pd.DataFrame({"stock": close, "spy": spy_close}).dropna()
    if len(aligned) < days + 1:
        return []
    recent = aligned.iloc[-(days + 1):]
    daily_diff = (
        recent["stock"].pct_change().dropna() * 100
        - recent["spy"].pct_change().dropna() * 100
    )
    return [round(float(v), 2) for v in daily_diff.cumsum()]


def sparkline_data(close: pd.Series, days: int = 252) -> list[float]:
    """Last `days` close prices normalised to 100 for inline sparkline."""
    if close is None or close.empty:
        return []
    recent = close.iloc[-days:]
    if recent.empty or recent.iloc[0] == 0:
        return []
    return (recent / recent.iloc[0] * 100).round(2).tolist()


def build_row(
    ticker: str,
    meta: dict,
    history: dict[str, pd.Series],
    info: dict,
    all_history: dict[str, pd.Series],
    df_main: dict[str, pd.DataFrame] | None = None,
    rs_rank_val: int | None = None,
    rs_rank_prev: int | None = None,
) -> dict:
    """Assemble one table row for a given ticker."""
    close = history.get(ticker)
    inf   = info.get(ticker, {})
    df    = df_main.get(ticker) if df_main else None

    current_price = round(close.iloc[-1], 2) if close is not None and not close.empty else None
    price = current_price or 0

    sma20  = sma(close, 20)
    sma50  = sma(close, 50)
    sma200 = sma(close, 200)

    rs_delta: int | None = None
    if rs_rank_val is not None and rs_rank_prev is not None:
        rs_delta = rs_rank_val - rs_rank_prev

    tpe = inf.get("trailing_pe")
    fpe = inf.get("forward_pe")
    ps  = inf.get("ps_ratio")

    return {
        "ticker":        ticker,
        "company":       meta.get("company", inf.get("company_name", ticker)),
        "theme":         meta.get("theme", ""),
        "price":         current_price,
        "market_cap":    inf.get("market_cap"),
        "ps_ratio":      round(ps, 2)  if ps  else None,
        "trailing_pe":   round(tpe, 1) if tpe else None,
        "forward_pe":    round(fpe, 1) if fpe else None,
        "pct_ytd":       ytd_return(close),
        "pct_1y":        pct_return(close, 252),
        "pct_3m":        pct_return(close, 63),
        "pct_1m":        pct_return(close, 21),
        "pct_1d":        pct_return(close, 1),
        "pct_from_52h":  pct_from_high(close),
        "rs_rank":       rs_rank_val,
        "rs_delta":      rs_delta,
        "sma20":         sma20,
        "sma50":         sma50,
        "sma200":        sma200,
        "above_20":      price > sma20  if sma20  else False,
        "above_50":      price > sma50  if sma50  else False,
        "above_200":     price > sma200 if sma200 else False,
        "vol_ratio":     volume_ratio(df),
        "sparkline":     sparkline_data(close),
        "rs_spy_cum":    rs_spy_cumulative(close, all_history.get("SPY")),
        "earnings_date": inf.get("earnings_date"),
        "website":       inf.get("website", ""),
        "logo_url":      inf.get("logo_url", ""),
    }
