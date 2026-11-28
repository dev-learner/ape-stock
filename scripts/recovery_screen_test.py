# scripts/recovery_screen_test.py
# NAME: Recovery Screen Test
# DESC: Tests different parameter combinations for a recovery / U-turn screen.
# DETAIL: Identifies stocks that made a prior high, suffered a significant drawdown, and have since turned up. Parameters (look-back months, minimum drawdown %, recovery confirmation) are set at the top of the file so different combinations can be tried quickly. Prints the current candidates and basic stats. Read-only.
# ALLOW_DELETE: 1
# RUN: Tool2
# CATEGORY: analysis

"""
Recovery Screen Test
--------------------
Flexible tester for the recovery pattern:

1. Stock made a high within the look-back window.
2. Subsequently fell at least MIN_DRAWDOWN % from that high.
3. Has since recovered — currently above its 50-day MA and up at least
   RECOVERY_FROM_LOW % from the post-high low.

Edit the parameters at the top and re-run to compare results.
"""

import sqlite3
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta

# ========== PARAMETERS TO TEST ==========
LOOKBACK_MONTHS = 12          # how far back to look for the prior high
MIN_DRAWDOWN = 30.0           # minimum % fall from the high
RECOVERY_FROM_LOW = 15.0      # minimum % bounce from the low
REQUIRE_ABOVE_50MA = True     # must currently be above 50-day MA
MIN_MARKET_CAP = 500_000_000  # optional size filter (0 to disable)
# ========================================

DB_PATH = Path(__file__).parent.parent / "ape_stock.db"

def main():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    print(f"Recovery Screen Test")
    print(f"Look-back: {LOOKBACK_MONTHS} months | Min drawdown: {MIN_DRAWDOWN}% | "
          f"Recovery from low: {RECOVERY_FROM_LOW}% | Above 50MA: {REQUIRE_ABOVE_50MA}\n")

    # Load daily closes
    cur.execute("""
        SELECT symbol, date, close
        FROM daily_closes
        WHERE close IS NOT NULL
        ORDER BY symbol, date
    """)
    by_sym = defaultdict(list)
    for r in cur.fetchall():
        by_sym[r["symbol"]].append((r["date"], float(r["close"])))

    # Market caps
    cur.execute("SELECT symbol, market_cap FROM index_quotes")
    mcaps = {r["symbol"]: r["market_cap"] for r in cur.fetchall()}

    cutoff = (datetime.now() - timedelta(days=LOOKBACK_MONTHS * 30)).strftime("%Y-%m-%d")
    candidates = []

    for sym, series in by_sym.items():
        if len(series) < 100:
            continue
        if MIN_MARKET_CAP and (mcaps.get(sym) or 0) < MIN_MARKET_CAP:
            continue

        dates = [d for d, c in series]
        closes = [c for d, c in series]

        # Find highest high in the look-back window
        window = [(d, c) for d, c in series if d >= cutoff]
        if not window:
            continue
        high_date, high_price = max(window, key=lambda x: x[1])
        high_idx = dates.index(high_date)

        # Lowest point after the high
        post_high = closes[high_idx:]
        if not post_high:
            continue
        low_price = min(post_high)
        low_idx = high_idx + post_high.index(low_price)
        drawdown = (low_price / high_price - 1) * 100

        if drawdown > -MIN_DRAWDOWN:
            continue

        # Current recovery
        current = closes[-1]
        bounce = (current / low_price - 1) * 100
        if bounce < RECOVERY_FROM_LOW:
            continue

        # 50-day MA check
        if REQUIRE_ABOVE_50MA and len(closes) >= 50:
            ma50 = sum(closes[-50:]) / 50
            if current <= ma50:
                continue

        candidates.append({
            "symbol": sym,
            "high_date": high_date,
            "high": high_price,
            "low_date": dates[low_idx],
            "low": low_price,
            "drawdown": drawdown,
            "current": current,
            "bounce": bounce,
            "mcap": mcaps.get(sym)
        })

    candidates.sort(key=lambda x: x["bounce"], reverse=True)

    print(f"Candidates found: {len(candidates)}\n")
    if candidates:
        print(f"{'Symbol':<8} {'High Date':<12} {'Drawdown':>9} {'Bounce':>7} {'Current':>8}")
        print("-" * 50)
        for c in candidates:
            print(f"{c['symbol']:<8} {c['high_date']:<12} {c['drawdown']:9.1f}% {c['bounce']:7.1f}% {c['current']:8.1f}")

    conn.close()
    print("\nDone. Adjust parameters at top of file and re-run to test other combinations.")

if __name__ == "__main__":
    main()