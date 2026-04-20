"""
Persist daily RS Rank snapshots to SQLite so we can show rank trends over time.
The DB file lives alongside this module and is gitignored.
"""

import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "rs_history.db"


def _init() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rs_snapshots (
                ticker  TEXT    NOT NULL,
                date    TEXT    NOT NULL,
                rs_rank INTEGER NOT NULL,
                PRIMARY KEY (ticker, date)
            )
        """)


def save_snapshot(rs_ranks: dict[str, int | None]) -> None:
    """Persist today's RS ranks. Idempotent — safe to call on every app load."""
    today = str(date.today())
    _init()
    rows = [(t, today, r) for t, r in rs_ranks.items() if r is not None]
    if not rows:
        return
    with sqlite3.connect(DB_PATH) as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO rs_snapshots (ticker, date, rs_rank) VALUES (?, ?, ?)",
            rows,
        )


def load_prev_snapshot(days_back: int = 5) -> dict[str, int]:
    """
    Return the most recent RS snapshot taken at least `days_back` days ago.
    Returns {} if no prior data exists yet (first run).
    """
    cutoff = str(date.today() - timedelta(days=days_back))
    _init()
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT MAX(date) FROM rs_snapshots WHERE date <= ?", (cutoff,)
        ).fetchone()
        if not row or row[0] is None:
            return {}
        best_date = row[0]
        rows = conn.execute(
            "SELECT ticker, rs_rank FROM rs_snapshots WHERE date = ?", (best_date,)
        ).fetchall()
    return {ticker: rank for ticker, rank in rows}
