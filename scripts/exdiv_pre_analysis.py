# scripts/exdiv_pre_analysis.py
# DESC: Analyse price behaviour in the 5 days before ex-dividend dates
# RUN: Tool2

import sqlite3
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta

db_path = Path(__file__).parent.parent / "ape_stock.db"
conn = sqlite3.connect(db_path, timeout=30)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("Loading ex-dividend dates...")
cur.execute("""
    SELECT symbol, ex_dividend_date, dividend_yield
    FROM index_quotes
    WHERE ex_dividend_date IS NOT NULL
      AND ex_dividend_date != ''
""")
exdivs = cur.fetchall()

print("Loading daily closes...")
cur.execute("""
    SELECT symbol, date, close
    FROM daily_closes
    WHERE close IS NOT NULL
    ORDER BY symbol, date
""")
by_sym = defaultdict(list)
for r in cur.fetchall():
    by_sym[r["symbol"]].append((r["date"], r["close"]))

# Build date-indexed lookup per symbol
sym_dates = {}
for sym, series in by_sym.items():
    sym_dates[sym] = {d: c for d, c in series}

print(f"Found {len(exdivs)} symbols with an ex-div date")

# Collect returns for T-5 ... T-1 and a simple control (T-10)
days_before = [5, 4, 3, 2, 1]
results = {d: [] for d in days_before}
control = []
yield_buckets = {"low": [], "mid": [], "high": []}  # <1%, 1-3%, >3%

events = 0
for row in exdivs:
    sym = row["symbol"]
    ex_str = row["ex_dividend_date"]
    dy = row["dividend_yield"] or 0
    if sym not in sym_dates:
        continue
    try:
        ex_dt = datetime.fromisoformat(ex_str[:10]).date()
    except Exception:
        continue

    dates = sym_dates[sym]
    # Find trading days around the ex-date
    # We need the close on the day before each offset
    sorted_dates = sorted(dates.keys())
    # Locate the last trading day strictly before ex_dt
    pre_dates = [d for d in sorted_dates if d < ex_dt.isoformat()]
    if len(pre_dates) < 6:
        continue

    events += 1
    # T-1 is the last pre_date, T-2 the one before, etc.
    for offset in days_before:
        if len(pre_dates) >= offset + 1:
            d_now = pre_dates[-offset]
            d_prev = pre_dates[-offset - 1]
            c_now = dates[d_now]
            c_prev = dates[d_prev]
            if c_prev:
                ret = (c_now - c_prev) / c_prev * 100
                results[offset].append(ret)
                # bucket by yield
                if dy < 1:
                    yield_buckets["low"].append((offset, ret))
                elif dy < 3:
                    yield_buckets["mid"].append((offset, ret))
                else:
                    yield_buckets["high"].append((offset, ret))

    # crude control: return on T-10 if available
    if len(pre_dates) >= 11:
        d_now = pre_dates[-10]
        d_prev = pre_dates[-11]
        c_now = dates[d_now]
        c_prev = dates[d_prev]
        if c_prev:
            control.append((c_now - c_prev) / c_prev * 100)

def stats(vals):
    if not vals:
        return 0, 0.0, 0.0
    avg = sum(vals) / len(vals)
    wins = sum(1 for v in vals if v > 0) / len(vals) * 100
    return len(vals), avg, wins

print(f"\nEvents with sufficient history: {events}")
print(f"{'Days before':>12} {'N':>6} {'Avg%':>8} {'Win%':>7}")
print("-" * 36)
for d in days_before:
    n, avg, win = stats(results[d])
    print(f"{d:12} {n:6} {avg:8.3f} {win:7.1f}")

n, avg, win = stats(control)
print(f"{'Control T-10':>12} {n:6} {avg:8.3f} {win:7.1f}")

print("\nBy dividend yield (T-1 only):")
for label, pairs in yield_buckets.items():
    t1 = [r for off, r in pairs if off == 1]
    n, avg, win = stats(t1)
    print(f"  {label:<5} N={n:4}  Avg={avg:7.3f}%  Win={win:5.1f}%")

conn.close()
print("\nNote: limited by one year of daily data and a single stored ex-date per symbol.")