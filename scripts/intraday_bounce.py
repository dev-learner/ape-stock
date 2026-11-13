# scripts/intraday_bounce.py
# DESC: Realistic-entry test of same-day/next-day bounce after large intraday drops (snapshots_5min)
# RUN: Tool2

import sqlite3
from pathlib import Path
from collections import defaultdict
from datetime import datetime

db_path = Path(__file__).parent.parent / "ape_stock.db"
conn = sqlite3.connect(db_path, timeout=30)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("Loading 5-min snapshots...")
cur.execute("""
    SELECT symbol, ts, price
    FROM snapshots_5min
    WHERE price IS NOT NULL
    ORDER BY symbol, ts
""")
rows = cur.fetchall()

by_sym_date = defaultdict(lambda: defaultdict(list))
for r in rows:
    try:
        dt = datetime.fromisoformat(r["ts"])
        date_str = dt.date().isoformat()
        by_sym_date[r["symbol"]][date_str].append((dt, r["price"]))
    except Exception:
        continue

print(f"Symbols with data: {len(by_sym_date)}")

DROP_PCTS = [5, 6, 7, 8]
STAMP = 0.5  # percent

results = {p: {"signals": 0, "same_day": [], "next_day": []} for p in DROP_PCTS}

for sym, dates in by_sym_date.items():
    sorted_dates = sorted(dates.keys())
    for i, date in enumerate(sorted_dates):
        bars = sorted(dates[date])
        if len(bars) < 8:
            continue
        prices = [b[1] for b in bars]
        day_open = prices[0]

        # Find first bar that crosses each drop threshold from the open
        for thresh in DROP_PCTS:
            entry_price = None
            for p in prices:
                drop = (p - day_open) / day_open * 100 if day_open else 0
                if drop <= -thresh:
                    entry_price = p          # buy at the close of this 5-min bar
                    break
            if entry_price is None:
                continue

            results[thresh]["signals"] += 1
            day_close = prices[-1]

            # same-day net from realistic entry
            same_gross = (day_close - entry_price) / entry_price * 100
            results[thresh]["same_day"].append(same_gross - STAMP)

            # next-day close
            if i + 1 < len(sorted_dates):
                next_bars = sorted(dates[sorted_dates[i + 1]])
                if next_bars:
                    next_close = next_bars[-1][1]
                    next_gross = (next_close - entry_price) / entry_price * 100
                    results[thresh]["next_day"].append(next_gross - STAMP)

print("\nRealistic entry (first 5-min bar that crosses drop from open) after 0.5% stamp")
print(f"{'Drop>=':>7} {'Signals':>8} {'SameDay Avg%':>13} {'SameDay Med%':>13} "
      f"{'NextDay Avg%':>13} {'NextDay Med%':>13}")
print("-" * 75)

for thresh in DROP_PCTS:
    r = results[thresh]
    def avg(xs): return sum(xs) / len(xs) if xs else 0
    def med(xs):
        if not xs: return 0
        s = sorted(xs)
        return s[len(s) // 2]
    print(f"{thresh:7} {r['signals']:8} {avg(r['same_day']):13.2f} {med(r['same_day']):13.2f} "
          f"{avg(r['next_day']):13.2f} {med(r['next_day']):13.2f}")

conn.close()
print("\nEntry = close of the 5-min bar that first reaches the drop threshold from the day's open.")
print("Returns are net of 0.5% stamp. Spread/slippage not included.")