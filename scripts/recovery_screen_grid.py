# scripts/recovery_screen_grid.py
# NAME: Recovery Screen Grid Search
# DESC: Tests a grid of recovery-screen parameters and summarises the results.
# DETAIL: Runs every combination of look-back (6/9/12 months), minimum drawdown (25/30/35/40 %) and recovery-from-low (10/15/20 %). For each combination reports the number of candidates and the top 5 symbols by bounce. Requires stocks to be above the 50-day MA. Read-only. Use the summary to choose the most meaningful parameter set.
# ALLOW_DELETE: 1
# RUN: Tool2
# CATEGORY: analysis

"""
Recovery Screen Grid Search
---------------------------
Tests 36 parameter combinations and prints a compact summary for each.
"""

import sqlite3
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta

DB_PATH = Path(__file__).parent.parent / "ape_stock.db"

LOOKBACKS = [6, 9, 12]
DRAWDOWNS = [25.0, 30.0, 35.0, 40.0]
RECOVERIES = [10.0, 15.0, 20.0]
REQUIRE_ABOVE_50MA = True
MIN_MARKET_CAP = 500_000_000

def screen(conn, lookback_months, min_drawdown, recovery_from_low):
    cur = conn.cursor()
    cur.execute("""
        SELECT symbol, date, close
        FROM daily_closes
        WHERE close IS NOT NULL
        ORDER BY symbol, date
    """)
    by_sym = defaultdict(list)
    for r in cur.fetchall():
        by_sym[r["symbol"]].append((r["date"], float(r["close"])))

    cur.execute("SELECT symbol, market_cap FROM index_quotes")
    mcaps = {r["symbol"]: r["market_cap"] for r in cur.fetchall()}

    cutoff = (datetime.now() - timedelta(days=lookback_months * 30)).strftime("%Y-%m-%d")
    candidates = []

    for sym, series in by_sym.items():
        if len(series) < 100:
            continue
        if MIN_MARKET_CAP and (mcaps.get(sym) or 0) < MIN_MARKET_CAP:
            continue

        dates = [d for d, c in series]
        closes = [c for d, c in series]

        window = [(d, c) for d, c in series if d >= cutoff]
        if not window:
            continue
        high_date, high_price = max(window, key=lambda x: x[1])
        high_idx = dates.index(high_date)

        post_high = closes[high_idx:]
        if not post_high:
            continue
        low_price = min(post_high)
        drawdown = (low_price / high_price - 1) * 100
        if drawdown > -min_drawdown:
            continue

        current = closes[-1]
        bounce = (current / low_price - 1) * 100
        if bounce < recovery_from_low:
            continue

        if REQUIRE_ABOVE_50MA and len(closes) >= 50:
            ma50 = sum(closes[-50:]) / 50
            if current <= ma50:
                continue

        candidates.append({
            "symbol": sym,
            "drawdown": drawdown,
            "bounce": bounce
        })

    candidates.sort(key=lambda x: x["bounce"], reverse=True)
    return candidates

def main():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row

    print("Recovery Screen Grid Search")
    print(f"Look-backs: {LOOKBACKS} | Drawdowns: {DRAWDOWNS} | Recoveries: {RECOVERIES}")
    print(f"Above 50MA: {REQUIRE_ABOVE_50MA} | Min market cap: £{MIN_MARKET_CAP/1e6:.0f}m\n")

    print(f"{'Lookbk':>6} {'Drwdn':>6} {'Recov':>6} {'Count':>6}  Top 5 by bounce")
    print("-" * 70)

    for lb in LOOKBACKS:
        for dd in DRAWDOWNS:
            for rec in RECOVERIES:
                cands = screen(conn, lb, dd, rec)
                top5 = ", ".join(c["symbol"] for c in cands[:5]) if cands else "-"
                print(f"{lb:6} {dd:6.0f} {rec:6.0f} {len(cands):6}  {top5}")

    conn.close()
    print("\nDone.")

if __name__ == "__main__":
    main()