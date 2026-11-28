# scripts/recovery_screen.py
# NAME: Recovery Screen
# DESC: Lists stocks that have recovered from a deep drawdown using locked parameters, with current rank.
# DETAIL: Identifies FTSE names that made a high in the last 12 months, fell at least 35 % from that high, have since bounced at least 15 % from the low, and are currently above their 50-day moving average. Minimum market cap £500 m. Shows high/low dates and prices, absolute and percentage drawdown/bounce, current price, and the stock’s current position in the full Screener ranking (if ranked). Read-only.
# ALLOW_DELETE: 0
# RUN: Tool2
# CATEGORY: uncategorised

"""
Recovery Screen
---------------
Locked parameters:
- Look-back: 12 months
- Minimum drawdown: 35 %
- Recovery from low: 15 %
- Must be above 50-day MA
- Minimum market cap: £500 m

Also shows the current full-rank position from daily_ranks.
"""

import sqlite3
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta

DB_PATH = Path(__file__).parent.parent / "ape_stock.db"

LOOKBACK_MONTHS = 12
MIN_DRAWDOWN = 35.0
RECOVERY_FROM_LOW = 15.0
REQUIRE_ABOVE_50MA = True
MIN_MARKET_CAP = 500_000_000

def main():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    print("Recovery Screen")
    print(f"Look-back: {LOOKBACK_MONTHS} months | Min drawdown: {MIN_DRAWDOWN}% | "
          f"Recovery from low: {RECOVERY_FROM_LOW}% | Above 50MA: {REQUIRE_ABOVE_50MA}")
    print(f"Min market cap: £{MIN_MARKET_CAP/1e6:.0f}m\n")

    # Price history
    cur.execute("""
        SELECT symbol, date, close
        FROM daily_closes
        WHERE close IS NOT NULL
        ORDER BY symbol, date
    """)
    by_sym = defaultdict(list)
    for r in cur.fetchall():
        by_sym[r["symbol"]].append((r["date"], float(r["close"])))

    # Names and market caps
    cur.execute("SELECT symbol, market_cap, name FROM index_quotes")
    meta = {r["symbol"]: {"mcap": r["market_cap"], "name": r["name"]} for r in cur.fetchall()}

    # Latest full ranks
    cur.execute("SELECT MAX(date) FROM daily_ranks")
    rank_date = cur.fetchone()[0]
    ranks = {}
    if rank_date:
        cur.execute("SELECT symbol, rank FROM daily_ranks WHERE date = ?", (rank_date,))
        ranks = {r["symbol"]: r["rank"] for r in cur.fetchall()}

    cutoff = (datetime.now() - timedelta(days=LOOKBACK_MONTHS * 30)).strftime("%Y-%m-%d")
    candidates = []

    for sym, series in by_sym.items():
        if len(series) < 100:
            continue
        info = meta.get(sym, {})
        if MIN_MARKET_CAP and (info.get("mcap") or 0) < MIN_MARKET_CAP:
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
        low_idx = high_idx + post_high.index(low_price)
        low_date = dates[low_idx]
        drawdown_abs = high_price - low_price
        drawdown_pct = (low_price / high_price - 1) * 100
        if drawdown_pct > -MIN_DRAWDOWN:
            continue

        current = closes[-1]
        bounce_abs = current - low_price
        bounce_pct = (current / low_price - 1) * 100
        if bounce_pct < RECOVERY_FROM_LOW:
            continue

        if REQUIRE_ABOVE_50MA and len(closes) >= 50:
            ma50 = sum(closes[-50:]) / 50
            if current <= ma50:
                continue

        candidates.append({
            "symbol": sym,
            "name": (info.get("name") or "")[:28],
            "high_date": high_date,
            "high_price": high_price,
            "low_date": low_date,
            "low_price": low_price,
            "drawdown_abs": drawdown_abs,
            "drawdown_pct": drawdown_pct,
            "bounce_abs": bounce_abs,
            "bounce_pct": bounce_pct,
            "current": current,
            "rank": ranks.get(sym)
        })

    candidates.sort(key=lambda x: x["bounce_pct"], reverse=True)

    print(f"Candidates found: {len(candidates)}\n")
    if not candidates:
        print("None.")
    else:
        print(f"{'Symbol':<8} {'Name':<28} {'High Date':<12} {'High':>8} {'Low Date':<12} {'Low':>8} "
              f"{'Drwdn':>8} {'Drwdn%':>7} {'Bnce':>8} {'Bnce%':>7} {'Current':>8} {'Rank':>5}")
        print("-" * 136)
        for c in candidates:
            rank_str = str(c["rank"]) if c["rank"] is not None else "-"
            print(f"{c['symbol']:<8} {c['name']:<28} {c['high_date']:<12} {c['high_price']:8.1f} "
                  f"{c['low_date']:<12} {c['low_price']:8.1f} "
                  f"{c['drawdown_abs']:8.1f} {c['drawdown_pct']:7.1f}% "
                  f"{c['bounce_abs']:8.1f} {c['bounce_pct']:7.1f}% {c['current']:8.1f} {rank_str:>5}")

    conn.close()
    print("\nDone.")

if __name__ == "__main__":
    main()