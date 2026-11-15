# scripts/screener_rank_persistence_grid.py
# DESC: Full persistence-window x rank-cutoff grid (5-90 step 5) for Screener target/stop
# RUN: Tool2

import sqlite3
from pathlib import Path
from collections import defaultdict

db_path = Path(__file__).parent.parent / "ape_stock.db"

TARGET_PCT = 10.0
STOP_PCT = 10.0
RANK_CUTOFFS = [5, 8, 10, 12, 15, 20]
PERSISTENCE_WINDOWS = list(range(5, 95, 5))   # 5, 10, 15 ... 90
NOTIONAL = 500.0
STAMP = 0.005
START_DATE = "2026-02-01"

print("Screener persistence-window x rank-cutoff grid")
print("-" * 50)
print(f"Target +{TARGET_PCT}% / Stop -{STOP_PCT}%")
print(f"Rank cut-offs: {RANK_CUTOFFS}")
print(f"Persistence windows: {PERSISTENCE_WINDOWS}")
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
conn.close()

sorted_dates = sorted(all_dates)
start_idx = next((i for i, d in enumerate(sorted_dates) if d >= START_DATE), 0)
print(f"Simulation window: {sorted_dates[start_idx]} to {sorted_dates[-1]} ({len(sorted_dates) - start_idx} days)")
print()

def build_screener(as_of_date):
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
        candidates.append((sym, ret_3m, closes[-1]))
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates

def compute_scores(rank_n, window):
    """Count appearances in top-N over the trailing 'window' trading days."""
    scores = defaultdict(int)
    for i in range(start_idx, len(sorted_dates)):
        today = sorted_dates[i]
        # look-back window
        from_idx = max(start_idx, i - window + 1)
        for j in range(from_idx, i + 1):
            d = sorted_dates[j]
            screener = build_screener(d)
            for sym, _, _ in screener[:rank_n]:
                scores[sym] += 1
    return set(scores.keys())

def run_simulation(ranked_set):
    positions = {}
    trades = []

    for i in range(start_idx, len(sorted_dates)):
        today = sorted_dates[i]
        screener = build_screener(today)

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
            if ranked_set is not None and sym not in ranked_set:
                continue
            shares = NOTIONAL / price
            positions[sym] = (price, today, shares)

    # force-close
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

# --- unrestricted baseline ---
print("Running unrestricted baseline...")
unrestricted_trades = run_simulation(ranked_set=None)
u_trades, u_win, u_pnl, u_roi = summarise(unrestricted_trades)
print(f"Unrestricted: {u_trades} trades, {u_win:.1f}% win, P&L £{u_pnl:.2f}, ROI {u_roi:.1f}%")
print()

# --- full grid ---
print("Running full grid (this will take a few minutes)...")
all_results = []

for window in PERSISTENCE_WINDOWS:
    print(f"\n=== Persistence window: {window} days ===")
    print(f"{'Cut-off':>8} {'Trades':>8} {'Win%':>8} {'P&L':>12} {'ROI%':>8}")
    print("-" * 48)
    window_best = None
    for n in RANK_CUTOFFS:
        ranked_set = compute_scores(n, window)
        trades = run_simulation(ranked_set)
        n_trades, win, pnl, roi = summarise(trades)
        print(f"{n:>8} {n_trades:>8} {win:>7.1f}% {pnl:>11.2f} {roi:>7.1f}%")
        rec = {"window": window, "cutoff": n, "trades": n_trades,
               "win_rate": win, "pnl": pnl, "roi": roi}
        all_results.append(rec)
        if window_best is None or roi > window_best["roi"]:
            window_best = rec
    print(f"Best in this window: cut-off {window_best['cutoff']} -> {window_best['roi']:.1f}%")

# --- overall summary ---
print("\n" + "=" * 60)
print("OVERALL BEST BY ROI")
print("=" * 60)
overall_best = max(all_results, key=lambda x: x["roi"])
print(f"Window {overall_best['window']} days, cut-off {overall_best['cutoff']}")
print(f"Trades: {overall_best['trades']}, Win: {overall_best['win_rate']:.1f}%, "
      f"P&L: £{overall_best['pnl']:.2f}, ROI: {overall_best['roi']:.1f}%")

# Top 5 combinations
print("\nTop 5 combinations:")
for i, r in enumerate(sorted(all_results, key=lambda x: x["roi"], reverse=True)[:5], 1):
    print(f"  {i}. window={r['window']:>2}, cut-off={r['cutoff']:>2} -> "
          f"ROI {r['roi']:.1f}%  ({r['trades']} trades, {r['win_rate']:.1f}% win)")

print("\nDone.")