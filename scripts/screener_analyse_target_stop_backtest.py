# scripts/screener_analyse_target_stop_backtest.py
# DESC: Focused grid-search of Screener target/stop with ranking filter
# RUN: From venv/cmd

import sqlite3
from pathlib import Path
from collections import defaultdict
import itertools

db_path = Path(__file__).parent.parent / "ape_stock.db"

print("Screener target/stop focused grid (restrict = yes)")
print("-" * 50)

# --- load data once ---
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
start_idx = next((i for i, d in enumerate(sorted_dates) if d >= "2026-02-01"), 0)

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

def compute_scores(rank_n):
    scores = defaultdict(int)
    for i in range(start_idx, len(sorted_dates)):
        today = sorted_dates[i]
        screener = build_screener(today)
        for sym, _, _ in screener[:rank_n]:
            scores[sym] += 1
    return set(scores.keys())

def run_simulation(ranked_set, target_pct, stop_pct):
    positions = {}
    trades = []
    notional = 500.0
    stamp = 0.005

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
            if ret >= target_pct or ret <= -stop_pct:
                gross = shares * today_close
                cost = notional * (1 + stamp)
                pnl = gross - cost
                trades.append(pnl)
                to_close.append(sym)
        for sym in to_close:
            del positions[sym]

        for sym, _, price in screener:
            if sym in positions or sym not in ranked_set:
                continue
            shares = notional / price
            positions[sym] = (price, today, shares)

    last_date = sorted_dates[-1]
    for sym, (entry, entry_date, shares) in positions.items():
        series = by_sym.get(sym, [])
        last_close = series[-1][1] if series else entry
        gross = shares * last_close
        cost = notional * (1 + stamp)
        trades.append(gross - cost)

    if not trades:
        return 0, 0.0, 0.0
    wins = sum(1 for p in trades if p > 0)
    total_pnl = sum(trades)
    return len(trades), wins / len(trades) * 100, total_pnl

# --- focused grid ---
rank_ns = [5, 10, 15]
targets = [5, 6, 7, 8, 10, 12]
stops = [4, 5, 6, 8, 10]

print(f"Grid: {len(rank_ns)} ranks × {len(targets)} targets × {len(stops)} stops = {len(rank_ns)*len(targets)*len(stops)} runs\n")

results = []
for rank_n in rank_ns:
    print(f"Ranking top-{rank_n}...")
    ranked_set = compute_scores(rank_n)
    for target, stop in itertools.product(targets, stops):
        n_trades, win_rate, total_pnl = run_simulation(ranked_set, target, stop)
        results.append({
            "rank_n": rank_n,
            "target": target,
            "stop": stop,
            "trades": n_trades,
            "win_rate": win_rate,
            "pnl": total_pnl,
            "roi": total_pnl / 500 * 100
        })

results.sort(key=lambda x: x["pnl"], reverse=True)

print("\n=== Top 15 parameter sets (by total P&L) ===")
print(f"{'Rank':>4} {'Target':>7} {'Stop':>6} {'Trades':>7} {'Win%':>6} {'P&L':>10} {'ROI%':>7}")
print("-" * 55)
for r in results[:15]:
    print(f"{r['rank_n']:>4} {r['target']:>7} {r['stop']:>6} {r['trades']:>7} {r['win_rate']:>6.1f} {r['pnl']:>10.0f} {r['roi']:>7.1f}")

print(f"\nTotal combinations tested: {len(results)}")
print("Done.")