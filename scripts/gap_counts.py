# scripts/gap_counts.py
# DESC: Count gap-ups and gap-downs (open vs prev close) for every stock, with current rank
# RUN: Tool2

"""
Analyses all stocks in daily_closes and reports, for each symbol:

- Number of gap-up days (open >= previous close + threshold %)
- Number of gap-down days (open <= previous close - threshold %)
- Total gap days
- Company name (when present in index_quotes)
- Current rank (most recent rank from daily_ranks, or - if none)

A gap is measured from the previous session's close to the current session's open.
The threshold percentage is set by the GAP_THRESHOLD constant below.
Stocks with fewer than MIN_DAYS of usable history are omitted.
Output is a clean aligned table sorted by total gaps (highest first).
"""

import sqlite3
from pathlib import Path
from collections import defaultdict

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
GAP_THRESHOLD = 3.0          # percent; change as desired (e.g. 2.0, 5.0)
MIN_DAYS = 10                # minimum number of trading days required
DB_NAME = "ape_stock.db"

# ---------------------------------------------------------------------------
# Connect and load data
# ---------------------------------------------------------------------------
db_path = Path(__file__).parent.parent / DB_NAME
conn = sqlite3.connect(db_path, timeout=30)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("Loading daily closes (open & close)...")
cur.execute("""
    SELECT symbol, date, open, close
    FROM daily_closes
    WHERE open IS NOT NULL
      AND close IS NOT NULL
      AND open > 0
      AND close > 0
    ORDER BY symbol, date
""")
rows = cur.fetchall()

# Group by symbol
by_sym = defaultdict(list)
for r in rows:
    by_sym[r["symbol"]].append(r)

# Optional: company names
cur.execute("SELECT symbol, name FROM index_quotes")
names = {r["symbol"]: r["name"] for r in cur.fetchall() if r["name"]}

# Current ranks (most recent date per symbol)
print("Loading current ranks...")
cur.execute("""
    SELECT symbol, rank
    FROM daily_ranks
    WHERE date = (SELECT MAX(date) FROM daily_ranks)
""")
ranks = {r["symbol"]: r["rank"] for r in cur.fetchall()}

# ---------------------------------------------------------------------------
# Count gaps per symbol
# ---------------------------------------------------------------------------
results = []

for symbol, data in by_sym.items():
    if len(data) < MIN_DAYS:
        continue

    gap_up = 0
    gap_down = 0

    for i in range(1, len(data)):
        prev_close = data[i - 1]["close"]
        today_open = data[i]["open"]

        if prev_close is None or prev_close == 0 or today_open is None:
            continue

        gap_pct = (today_open - prev_close) / prev_close * 100.0

        if gap_pct >= GAP_THRESHOLD:
            gap_up += 1
        elif gap_pct <= -GAP_THRESHOLD:
            gap_down += 1

    total = gap_up + gap_down
    if total == 0:
        continue

    name = names.get(symbol, "")
    rank = ranks.get(symbol)          # None if no current rank
    results.append((symbol, name, gap_up, gap_down, total, rank))

# Sort by total gaps descending, then by symbol
results.sort(key=lambda x: (-x[4], x[0]))

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
print(f"\nGap threshold: +/-{GAP_THRESHOLD:.1f}% (open vs previous close)")
print(f"Stocks analysed (with >= {MIN_DAYS} days): {len(by_sym)}")
print(f"Stocks with at least one gap: {len(results)}\n")

if not results:
    print("No gaps found.")
else:
    # Column widths
    sym_w = max(len("Symbol"), max(len(r[0]) for r in results))
    name_w = max(len("Name"), max(len(r[1]) for r in results) if any(r[1] for r in results) else 4)
    name_w = min(name_w, 32)   # keep table readable

    header = (
        f"{'Symbol':<{sym_w}}  "
        f"{'Name':<{name_w}}  "
        f"{'Gap Up':>8}  "
        f"{'Gap Down':>9}  "
        f"{'Total':>6}  "
        f"{'Rank':>5}"
    )
    print(header)
    print("-" * len(header))

    for symbol, name, up, down, total, rank in results:
        name_disp = (name[:name_w] if name else "")
        rank_disp = str(rank) if rank is not None else "-"
        print(
            f"{symbol:<{sym_w}}  "
            f"{name_disp:<{name_w}}  "
            f"{up:>8}  "
            f"{down:>9}  "
            f"{total:>6}  "
            f"{rank_disp:>5}"
        )

    # Summary totals
    total_up = sum(r[2] for r in results)
    total_down = sum(r[3] for r in results)
    print("-" * len(header))
    print(
        f"{'ALL':<{sym_w}}  "
        f"{'':<{name_w}}  "
        f"{total_up:>8}  "
        f"{total_down:>9}  "
        f"{total_up + total_down:>6}  "
        f"{'':>5}"
    )

conn.close()
print("\nDone.")