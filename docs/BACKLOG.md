# Backlog & Deferred Work

Items captured from development sessions. Move to GitHub Issues once repo is pushed.

---

## Infrastructure

- [ ] Push repo to GitHub (rename `master` → `main` first: `git branch -m master main`)
- [ ] Configure ruff as formatter/linter
- [ ] Add `.venv` and `__pycache__` to `.gitignore` on E drive repo
- [ ] Set up GitHub Actions CI (lint + basic smoke test)

## Data & Metrics

- [ ] Validate Forward P/E data quality — yfinance sometimes returns stale analyst estimates
- [ ] Add data freshness indicator (show when cache was last populated)
- [ ] Investigate logo gaps for small-cap tickers (RCAT, PDYN, LTBR etc.) — consider static `assets/logos/` fallback
- [ ] Consider adding volume data (relative volume vs 20-day avg)

## Dashboard UI

- [ ] Add screenshot to README for portfolio/showcase
- [ ] Test filter behaviour across all theme combinations
- [ ] Verify horizontal scroll works on mobile / narrow viewports
- [ ] Consider sticky header row for long stock lists
- [ ] Dark/light mode toggle

## Future Columns (evaluated, not yet added)

- [ ] Relative volume (today vs 20-day avg)
- [ ] Earnings date (next catalyst)
- [ ] Float / short interest %
- [ ] Sector ETF comparison (e.g. stock vs XAR for aerospace)

---

## Decisions Log

### 2026-03-23 — Initial build session

| Decision | Choice | Rationale |
|---|---|---|
| UI framework | Streamlit | Fastest prototyping; no frontend build step |
| Package manager | uv | 10–100× faster than pip; lockfile reproducibility |
| Table rendering | Single HTML `<table>` via `st.markdown` | Avoids Streamlit column padding, enables horizontal scroll, eliminates `st.components.v1` JS errors |
| RS Rank method | IBD quarterly weighted (0.4×Q4 + 0.2×Q3…) | Rewards recent momentum, not just raw 1Y return |
| RS vs SPY visual | 20 daily vertical bars (Excel-style) | More readable than cumulative line for 1M period; each bar = 1 trading day |
| Column sizing | Character-based auto-scaling | Adding a column auto-recalculates all widths; no manual tuning |
| Forward P/E negative | Display as n/a | Negative P/E (unprofitable forecast) is misleading if shown as a number |
| Filter layout | Flat `st.columns` (no expander) | Nesting multiselect inside expander + columns caused JS module load errors |
| Logo source | Yahoo Finance `logo_url` → Clearbit fallback | Yahoo is already in our data fetch; Clearbit covers gaps for large caps |
