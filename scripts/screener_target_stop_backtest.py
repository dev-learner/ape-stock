# scripts/screener_target_stop_backtest.py
# DESC: Back-test Screener entries with optional ranking filter and target/stop exits
# RUN: From venv/cmd (interactive prompts)

import sqlite3
from pathlib import Path
from collections import defaultdict
from datetime import datetime

db_path = Path(__file__).parent.parent / "ape_stock.db"

# --- prompts ---
print("Screener target/stop back-test")
print("-" * 40)

rank_n = 0
try:
    rank_input = input("Ranking top-N (5/10/15/20, or 0 to skip): ").strip()
    if rank_input in ("5", "10", "15", "20"):
        rank_n = int(rank_input)
except Exception:
    rank_n = 0

restrict = False
if rank_n > 0:
    r = input("Restrict buys to names that ranked in the top N? (y/n): ").strip().lower()
    restrict = r.startswith("y")

try:
    target_pct = float(input("Profit target % (e.g. 10): ") or "10")
    stop_pct = float(input("Stop loss % (e.g. 3): ") or "3")
except Exception:
    target_pct = 10.0
    stop_pct = 3.0

print(f"\nSettings: ranking={rank_n or 'off'}, restrict={restrict}, target=+{target_pct}%, stop=-{stop_pct}%\n")

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

# --- ranking pass ---
scores = defaultdict(int)
if rank_n > 0:
    print("Computing ranking scores...")
    for i in range(start_idx, len(sorted_dates)):
        today = sorted_dates[i]
        screener = build_screener(today)
        for sym, _, _ in screener[:rank_n]:
            scores[sym] += 1
    print("\n=== Ranking leader-board ===")
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    print(f"{'Symbol':<10} {'Days in top '+str(rank_n):>16}")
    print("-" * 28)
    for sym, sc in ranked[:30]:
        print(f"{sym:<10} {sc:>16}")
    print()

ranked_set = set(scores.keys()) if rank_n > 0 else set()

# --- trading simulation ---
def run_simulation(use_restrict):
    positions = {}  # symbol -> (entry_price, entry_date, shares)
    trades = []
    notional = 500.0
    stamp = 0.005

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
            if ret >= target_pct or ret <= -stop_pct:
                gross = shares * today_close
                cost = notional * (1 + stamp)
                pnl = gross - cost
                trades.append({
                    "symbol": sym,
                    "entry_date": entry_date,
                    "exit_date": today,
                    "ret": ret,
                    "pnl": pnl,
                    "reason": "target" if ret >= target_pct else "stop"
                })
                to_close.append(sym)
        for sym in to_close:
            del positions[sym]

        # entries
        for sym, ret_3m, price in screener:
            if sym in positions:
                continue
            if use_restrict and sym not in ranked_set:
                continue
            shares = notional / price
            positions[sym] = (price, today, shares)

    # force-close remaining
    last_date = sorted_dates[-1]
    for sym, (entry, entry_date, shares) in positions.items():
        series = by_sym.get(sym, [])
        last_close = series[-1][1] if series else entry
        ret = (last_close / entry - 1) * 100
        gross = shares * last_close
        cost = notional * (1 + stamp)
        pnl = gross - cost
        trades.append({
            "symbol": sym,
            "entry_date": entry_date,
            "exit_date": last_date,
            "ret": ret,
            "pnl": pnl,
            "reason": "open"
        })
    return trades

def print_results(trades, label):
    print(f"\n=== {label} (+{target_pct}% / -{stop_pct}%) ===")
    print(f"Trades: {len(trades)}")
    if not trades:
        print("No trades.")
        return
    wins = [t for t in trades if t["pnl"] > 0]
    total_pnl = sum(t["pnl"] for t in trades)
    print(f"Win rate: {len(wins)/len(trades)*100:.1f}%")
    print(f"Total P&L: £{total_pnl:.2f}")
    print(f"ROI on £500 base: {total_pnl/500*100:.1f}%")
    print("\nTop 5 winners:")
    for t in sorted(trades, key=lambda x: x["pnl"], reverse=True)[:5]:
        print(f"  {t['symbol']} {t['entry_date']} → {t['exit_date']}  {t['ret']:+.1f}%  £{t['pnl']:+.2f} ({t['reason']})")
    print("\nTop 5 losers:")
    for t in sorted(trades, key=lambda x: x["pnl"])[:5]:
        print(f"  {t['symbol']} {t['entry_date']} → {t['exit_date']}  {t['ret']:+.1f}%  £{t['pnl']:+.2f} ({t['reason']})")

print("Running simulations...")
unrestricted = run_simulation(use_restrict=False)
print_results(unrestricted, "Unrestricted")

if restrict:
    restricted = run_simulation(use_restrict=True)
    print_results(restricted, f"Restricted to top-{rank_n} ranked names")

print("\nDone.")