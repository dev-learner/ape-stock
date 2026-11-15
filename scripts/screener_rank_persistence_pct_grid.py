# scripts/screener_rank_persistence_pct_grid.py
# DESC: Three-way grid - rank cut-off x persistence window x min presence %
# RUN: External (long running)

import sqlite3
from pathlib import Path
from collections import defaultdict

db_path = Path(__file__).parent.parent / "ape_stock.db"

TARGET_PCT = 10.0
STOP_PCT = 10.0
RANK_CUTOFFS = [10, 12, 15]
PERSISTENCE_WINDOWS = list(range(5, 95, 5))   # 5, 10, ... 90
MIN_PRESENCE_PCTS = [30, 40, 50, 60, 70]
NOTIONAL = 500.0
STAMP = 0.005
START_DATE = "2026-02-01"

print("Screener rank x window x presence% grid")
print("-" * 50)
print(f"Target +{TARGET_PCT}% / Stop -{STOP_PCT}%")
print(f"Rank cut-offs: {RANK_CUTOFFS}")
print(f"Windows: {PERSISTENCE_WINDOWS}")
print(f"Min presence %: {MIN_PRESENCE_PCTS}")
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

print("Pre-computing daily Screener sets...")
daily_top = {}
for i in range(start_idx, len(sorted_dates)):
    d = sorted_dates[i]
    screener = build_screener(d)
    daily_top[d] = {sym for sym, _, _ in screener}
    if (i - start_idx) % 25 == 0:
        print(f"  ...{i - start_idx}/{len(sorted_dates) - start_idx}", flush=True)
print("Pre-compute done.\n")

def run_simulation(window, min_pct, rank_n):
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
                trades.append({"pnl": pnl})
                to_close.append(sym)
        for sym in to_close:
            del positions[sym]

        # entries
        top_n_set = {sym for sym, _, _ in screener[:rank_n]}
        for sym, ret_3m, price in screener:
            if sym in positions:
                continue
            from_idx = max(start_idx, i - window + 1)
            days = i - from_idx + 1
            needed = max(1, int(days * min_pct / 100.0))
            count = 0
            for j in range(from_idx, i + 1):
                d = sorted_dates[j]
                if sym in daily_top.get(d, set()):
                    count += 1
            if count < needed or sym not in top_n_set:
                continue
            shares = NOTIONAL / price
            positions[sym] = (price, today, shares)

    # force-close
    for sym, (entry, entry_date, shares) in positions.items():
        series = by_sym.get(sym, [])
        last_close = series[-1][1] if series else entry
        gross = shares * last_close
        cost = NOTIONAL * (1 + STAMP)
        pnl = gross - cost
        trades.append({"pnl": pnl})
    return trades

def summarise(trades):
    if not trades:
        return 0, 0.0, 0.0, 0.0
    wins = sum(1 for t in trades if t["pnl"] > 0)
    total_pnl = sum(t["pnl"] for t in trades)
    win_rate = wins / len(trades) * 100
    roi = total_pnl / NOTIONAL * 100
    return len(trades), win_rate, total_pnl, roi

# unrestricted baseline
print("Running unrestricted baseline...")
positions = {}
trades = []
for i in range(start_idx, len(sorted_dates)):
    today = sorted_dates[i]
    screener = build_screener(today)
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
            trades.append({"pnl": pnl})
            to_close.append(sym)
    for sym in to_close:
        del positions[sym]
    for sym, ret_3m, price in screener:
        if sym in positions:
            continue
        shares = NOTIONAL / price
        positions[sym] = (price, today, shares)
for sym, (entry, entry_date, shares) in positions.items():
    series = by_sym.get(sym, [])
    last_close = series[-1][1] if series else entry
    gross = shares * last_close
    cost = NOTIONAL * (1 + STAMP)
    pnl = gross - cost
    trades.append({"pnl": pnl})
u_trades, u_win, u_pnl, u_roi = summarise(trades)
print(f"Unrestricted: {u_trades} trades, {u_win:.1f}% win, P&L £{u_pnl:.2f}, ROI {u_roi:.1f}%\n")

# grid with interim reports
print("Running grid...")
all_results = []
best_so_far = None
total_combos = len(PERSISTENCE_WINDOWS) * len(MIN_PRESENCE_PCTS) * len(RANK_CUTOFFS)
done = 0

for window in PERSISTENCE_WINDOWS:
    print(f"\n=== Window {window} days ===")
    print(f"{'Pres%':>6} {'Cut':>4} {'Trades':>7} {'Win%':>7} {'P&L':>10} {'ROI%':>7}")
    print("-" * 48)
    for pct in MIN_PRESENCE_PCTS:
        for n in RANK_CUTOFFS:
            done += 1
            trades = run_simulation(window, pct, n)
            n_trades, win, pnl, roi = summarise(trades)
            rec = {
                "window": window, "pct": pct, "cutoff": n,
                "trades": n_trades, "win_rate": win, "pnl": pnl, "roi": roi
            }
            all_results.append(rec)
            print(f"{pct:>6} {n:>4} {n_trades:>7} {win:>6.1f}% {pnl:>9.2f} {roi:>6.1f}%")
            if best_so_far is None or roi > best_so_far["roi"]:
                best_so_far = rec
                print(f"  ** new best: window={window}, presence={pct}%, cut-off={n} -> {roi:.1f}% **")
    print(f"Best so far: window={best_so_far['window']}, presence={best_so_far['pct']}%, "
          f"cut-off={best_so_far['cutoff']} -> {best_so_far['roi']:.1f}%")

# final top 10
print("\n" + "=" * 70)
print("FINAL TOP 10 BY ROI")
print("=" * 70)
for i, r in enumerate(sorted(all_results, key=lambda x: x["roi"], reverse=True)[:10], 1):
    print(f"{i:2}. window={r['window']:>2}  presence={r['pct']:>2}%  cut-off={r['cutoff']:>2}  "
          f"-> ROI {r['roi']:6.1f}%  ({r['trades']:>3} trades, {r['win_rate']:4.1f}% win, P&L £{r['pnl']:7.2f})")

print("\nDone.")