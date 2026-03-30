import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def pct_return(close: pd.Series, days: int) -> float:
    """Return % change over the last `days` trading days."""
    if close is None or len(close) < 2:
        return None
    end = close.iloc[-1]
    start_idx = max(0, len(close) - days - 1)
    start = close.iloc[start_idx]
    if start == 0:
        return None
    return round((end - start) / start * 100, 2)


def ytd_return(close: pd.Series) -> float:
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
    """% below the 52-week high (negative = below high)."""
    h = high_52w(close)
    if h is None or close is None or close.empty:
        return None
    current = close.iloc[-1]
    return round((current - h) / h * 100, 2)


def rs_rank(ticker: str, history: dict[str, pd.Series]) -> int | None:
    """
    Relative Strength rank (1–99) vs all tickers in `history`.
    Uses the IBD-style 12-month performance with recency weighting:
      score = 0.4 * Q4_perf + 0.2 * Q3_perf + 0.2 * Q2_perf + 0.2 * Q1_perf
    """
    def _score(close: pd.Series) -> float | None:
        if close is None or len(close) < 50:
            return None
        n = len(close)
        q4 = (close.iloc[-1] / close.iloc[max(0, n - 63)] - 1) if n >= 63 else None
        q3 = (close.iloc[max(0, n - 63)] / close.iloc[max(0, n - 126)] - 1) if n >= 126 else None
        q2 = (close.iloc[max(0, n - 126)] / close.iloc[max(0, n - 189)] - 1) if n >= 189 else None
        q1 = (close.iloc[max(0, n - 189)] / close.iloc[max(0, n - 252)] - 1) if n >= 252 else None
        parts = [(q4, 0.4), (q3, 0.2), (q2, 0.2), (q1, 0.2)]
        total_weight = sum(w for v, w in parts if v is not None)
        if total_weight == 0:
            return None
        return sum(v * w for v, w in parts if v is not None) / total_weight

    scores = {t: _score(h) for t, h in history.items() if h is not None}
    scores = {t: s for t, s in scores.items() if s is not None}
    if ticker not in scores or len(scores) < 2:
        return None

    all_scores = sorted(scores.values())
    my_score = scores[ticker]
    rank_pct = np.searchsorted(all_scores, my_score, side="left") / len(all_scores)
    return max(1, min(99, int(rank_pct * 99) + 1))


def rs_spy_cumulative(close: pd.Series, spy_close: pd.Series, days: int = 20) -> list[float]:
    """
    Cumulative daily RS vs SPY over the last `days` trading days (~1 month).
    Returns a list of cumulative outperformance values (percentage points), starting near 0.
    A rising line = stock accelerating vs SPY; falling = fading.
    """
    if close is None or spy_close is None:
        return []
    aligned = pd.DataFrame({"stock": close, "spy": spy_close}).dropna()
    if len(aligned) < days + 1:
        return []
    recent = aligned.iloc[-(days + 1):]
    daily_diff = recent["stock"].pct_change().dropna() * 100 - recent["spy"].pct_change().dropna() * 100
    cumulative = [round(float(v), 2) for v in daily_diff.cumsum()]
    return cumulative


def sparkline_data(close: pd.Series, days: int = 252) -> list[float]:
    """Last `days` close prices normalised to 100 for inline sparkline."""
    if close is None or close.empty:
        return []
    recent = close.iloc[-days:]
    if recent.empty or recent.iloc[0] == 0:
        return []
    normalised = (recent / recent.iloc[0] * 100).round(2).tolist()
    return normalised


def build_row(ticker: str, meta: dict, history: dict, info: dict, all_history: dict) -> dict:
    """Assemble one table row for a given ticker."""
    close = history.get(ticker)
    inf = info.get(ticker, {})

    current_price = round(close.iloc[-1], 2) if close is not None and not close.empty else None
    mc  = inf.get("market_cap")
    ps  = inf.get("ps_ratio")
    tpe = inf.get("trailing_pe")
    fpe = inf.get("forward_pe")

    sma20  = sma(close, 20)
    sma50  = sma(close, 50)
    sma200 = sma(close, 200)

    price = current_price or 0

    return {
        "ticker":      ticker,
        "company":     meta.get("company", inf.get("company_name", ticker)),
        "theme":       meta.get("theme", ""),
        "price":       current_price,
        "market_cap":  mc,
        "ps_ratio":    round(ps, 2) if ps else None,
        "trailing_pe": round(tpe, 1) if tpe else None,
        "forward_pe":  round(fpe, 1) if fpe else None,
        "pct_ytd":     ytd_return(close),
        "pct_1y":      pct_return(close, 252),
        "pct_1m":      pct_return(close, 21),
        "high_52w":    high_52w(close),
        "pct_from_52h": pct_from_high(close),
        "rs_rank":     rs_rank(ticker, {t: h for t, h in all_history.items()}),
        "sma20":       sma20,
        "sma50":       sma50,
        "sma200":      sma200,
        "above_20":    price > sma20 if sma20 else False,
        "above_50":    price > sma50 if sma50 else False,
        "above_200":   price > sma200 if sma200 else False,
        "sparkline":      sparkline_data(close),
        "rs_spy_cum":     rs_spy_cumulative(close, all_history.get("SPY")),
        "website":        inf.get("website", ""),
        "logo_url":       inf.get("logo_url", ""),
    }
