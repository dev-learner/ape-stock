# scripts/screener_valuation_grid.py
# DESC: Grid-search PE / P/B / dividend filters on current fundamentals (LOOK-AHEAD)
# RUN: Tool2

"""
WARNING: This uses today's fundamentals applied to historical price paths.
Results contain look-ahead bias and are only useful for relative comparison
of filter settings, not as a pure historical back-test.
"""

import sqlite3
from pathlib import Path
from collections import defaultdict

print("Screener valuation filter grid (LOOK-AHEAD)")
print("=" * 50)
print("Uses current fundamentals snapshot on historical prices.")
print("Results are biased — use only for relative comparison.\n")

db_path = Path(__file__).parent.parent / "ape_stock.db"

# Fixed simulation parameters
TARGET_PCT = 10.0
STOP_PCT = 10.0
NOTIONAL = 500.0
STAMP = 0.005
START_DATE = "2026-02-01"

# Grid to search
PE_RANGES = [
    (None, None),          # no PE filter
    (5, 40),
    (5, 30),
    (8, 25),
    (10, 20),
]
PB_MAXES = [None, 5.0, 4.0, 3.0, 2.5]
REQUIRE_DIV = [False, True]

print(f"Target +{TARGET_PCT}% / Stop -{STOP_PCT}%")
print(f"PE ranges: {PE_RANGES}")
print(f"P/B maxes: {PB_MAXES}")
print(f"Require dividend: {REQUIRE_DIV}")
print()

# --- load data ---
conn = sqlite3.connect(db_path, timeout=60)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("Loading daily closes...")
cur.execute("""
    SELECT symbol, date, close
    FROM daily_closes
    WHERE close IS NOT NULL
    ORDER BY symbol, date
""")
by_sym = defaultdict(list)
all_dates = set()
for r in cur.fetchall():
    by_sym[r["symbol"]].append((r["date"], r["close"]))
    all_dates.add(r["date"])

cur.execute("SELECT symbol, market_cap FROM index_quotes")
meta = {r["symbol"]: r["market_cap"] for r in cur.fetchall()}

cur.execute("""
    SELECT symbol, pe_trailing, price_to_book, dividend_yield
    FROM fundamentals
""")
fund = {r["symbol"]: {
    "pe": r["pe_trailing"],
    "pb": r["price_to_book"],
    "div": r["dividend_yield"],
} for r in cur.fetchall()}

conn.close()

sorted_dates = sorted(all_dates)
start_idx = next((i for i, d in enumerate(sorted_dates) if d >= START_DATE), 0)
print(f"Simulation window: {sorted_dates[start_idx]} to {sorted_dates[-1]} "
      f"({len(sorted_dates) - start_idx} days)\n")

def passes_valuation(sym, pe_min, pe_max, pb_max, require_div):
    f = fund.get(sym)
    if not f:
        return True  # no fundamentals → allow (same as IS NULL behaviour)
    pe = f["pe"]
    pb = f["pb"]
    div = f["div"]
    if pe_min is not None and pe is not None and not (pe_min <= pe <= pe_max):
        return False
    if pb_max is not None and pb is not None and pb >= pb_max:
        return False
    if require_div and div is not None and div <= 0:
        return False
    return True

def build_screener(as_of_date, pe_min, pe_max, pb_max, require_div):
    candidates = []
    for sym, series in by_sym.items():
        closes = [c for d, c in series if d <= as_of_date]
        n = len(closes)
        if n < 200:
            continue
        ret_3m = (closes[-1] / closes[-63] - 1) * 100 if n > 63 and closes[-63] else None
        if ret_3m is None or ret_3m <= -15:
            continue
        ma50 = sum(closes[-50:]) / 50
        ma200 = sum(closes[-200:]) / 200
        if closes[-1] <= ma50 or closes[-1] <= ma200:
            continue
        mcap = meta.get(sym)
        if mcap is not None and mcap < 2_000_000_000:
            continue
        if not passes_valuation(sym, pe_min, pe_max, pb_max, require_div):
            continue
        candidates.append((sym, ret_3m, closes[-1]))
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates

def run_simulation(pe_min, pe_max, pb_max, require_div):
    positions = {}
    trades = []

    for i in range(start_idx, len(sorted_dates)):
        today = sorted_dates[i]
        screener = build_screener(today, pe_min, pe_max, pb_max, require_div)

        # exits
        to_close = []
        for sym, (entry, entry_date, shares) in list(positions.items()):
            series = by_sym.get(sym, [])
            today_close = next((c for d, c in series if d == today), None)
            if today_close is None:
                continue
            ret = (today_close / entry - 1) * 100
            if ret >= TARGET_PCT or ret <= -STOP_PCT:
                gross = shares * today_close
                cost = NOTIONAL * (1 + STAMP)
                pnl = gross - cost
                trades.append({"pnl": pnl, "ret": ret})
                to_close.append(sym)
        for sym in to_close:
            del positions[sym]

        # entries
        for sym, ret_3m, price in screener:
            if sym in positions:
                continue
            shares = NOTIONAL / price
            positions[sym] = (price, today, shares)

    # force-close remaining
    last_date = sorted_dates[-1]
    for sym, (entry, entry_date, shares) in positions.items():
        series = by_sym.get(sym, [])
        last_close = series[-1][1] if series else entry
        ret = (last_close / entry - 1) * 100
        gross = shares * last_close
        cost = NOTIONAL * (1 + STAMP)
        pnl = gross - cost
        trades.append({"pnl": pnl, "ret": ret})
    return trades

def summarise(trades):
    if not trades:
        return 0, 0.0, 0.0, 0.0
    wins = sum(1 for t in trades if t["pnl"] > 0)
    total_pnl = sum(t["pnl"] for t in trades)
    win_rate = wins / len(trades) * 100
    roi = total_pnl / NOTIONAL * 100
    return len(trades), win_rate, total_pnl, roi

# --- grid ---
results = []
total = len(PE_RANGES) * len(PB_MAXES) * len(REQUIRE_DIV)
n = 0
print(f"Running {total} combinations...\n")

for pe_min, pe_max in PE_RANGES:
    for pb_max in PB_MAXES:
        for require_div in REQUIRE_DIV:
            n += 1
            label_pe = f"{pe_min}-{pe_max}" if pe_min is not None else "none"
            label_pb = str(pb_max) if pb_max is not None else "none"
            print(f"  [{n}/{total}] PE={label_pe} P/B<{label_pb} Div={require_div}...", flush=True)
            trades = run_simulation(pe_min, pe_max, pb_max, require_div)
            n_trades, win, pnl, roi = summarise(trades)
            results.append({
                "pe": label_pe,
                "pb": label_pb,
                "div": require_div,
                "trades": n_trades,
                "win_rate": win,
                "pnl": pnl,
                "roi": roi,
            })

# --- report ---
results.sort(key=lambda x: x["roi"], reverse=True)

print("\n" + "=" * 78)
print(f"{'PE':>8} {'P/B':>6} {'Div':>5} {'Trades':>8} {'Win%':>8} {'P&L':>12} {'ROI%':>8}")
print("-" * 78)
for r in results:
    print(f"{r['pe']:>8} {r['pb']:>6} {str(r['div']):>5} "
          f"{r['trades']:>8} {r['win_rate']:>7.1f}% {r['pnl']:>11.2f} {r['roi']:>7.1f}%")
print("=" * 78)

best = results[0]
print(f"\nBest ROI: PE={best['pe']}  P/B<{best['pb']}  Div={best['div']}  "
      f"-> {best['roi']:.1f}%  (P&L £{best['pnl']:.2f}, {best['trades']} trades)")
print("\nDone. (Remember: look-ahead bias)")