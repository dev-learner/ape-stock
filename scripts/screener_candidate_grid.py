# scripts/screener_candidate_grid.py
# DESC: Grid-search candidate signal thresholds (rank fixed at 12)
# RUN: Tool2

"""
Grid-searches the four candidate-selection thresholds used by Tool 4's
"Show Candidates" logic. Rank cut-off is fixed at 12.

Note: these thresholds currently only affect on-screen signals.
This script tests whether applying them as additional entry filters
improves the target/stop results.
"""

import sqlite3
from pathlib import Path
from collections import defaultdict

print("Screener candidate-threshold grid")
print("=" * 50)
print("Rank cut-off fixed at 12")
print()

db_path = Path(__file__).parent.parent / "ape_stock.db"

# Fixed simulation parameters
TARGET_PCT = 10.0
STOP_PCT = 10.0
NOTIONAL = 500.0
STAMP = 0.005
START_DATE = "2026-02-01"
RANK_CUTOFF = 12

# Grid
VS50_BUY = [0, 1, 2, 3]
VS200_BUY = [0, 1, 2, 3]
VS50_HOLD = [0, -1, -2]
VS50_SELL = [0, -1, -2]
REQUIRE_FALLER = [True, False]

print(f"Target +{TARGET_PCT}% / Stop -{STOP_PCT}%")
print(f"vs50_buy: {VS50_BUY}")
print(f"vs200_buy: {VS200_BUY}")
print(f"vs50_hold: {VS50_HOLD}")
print(f"vs50_sell: {VS50_SELL}")
print(f"require_faller: {REQUIRE_FALLER}")
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
print(f"Simulation window: {sorted_dates[start_idx]} to {sorted_dates[-1]} "
      f"({len(sorted_dates) - start_idx} days)\n")

def build_screener(as_of_date):
    """Return list of (symbol, ret_3m, price, vs50, vs200) that pass base filters."""
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
        price = closes[-1]
        if price <= ma50 or price <= ma200:
            continue
        mcap = meta.get(sym)
        if mcap is not None and mcap < 2_000_000_000:
            continue
        vs50 = (price / ma50 - 1) * 100
        vs200 = (price / ma200 - 1) * 100
        candidates.append((sym, ret_3m, price, vs50, vs200))
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates

def compute_rank_scores():
    """Symbols that appear in top-RANK_CUTOFF at least once."""
    scores = defaultdict(int)
    for i in range(start_idx, len(sorted_dates)):
        today = sorted_dates[i]
        screener = build_screener(today)
        for sym, _, _, _, _ in screener[:RANK_CUTOFF]:
            scores[sym] += 1
    return set(scores.keys())

print("Computing rank scores...")
ranked_set = compute_rank_scores()
print(f"Names that ranked in top {RANK_CUTOFF} at least once: {len(ranked_set)}\n")

def passes_candidate(vs50, vs200, is_faller, vs50_buy, vs200_buy, vs50_hold, vs50_sell, require_faller):
    """Return signal: 'buy', 'hold', 'sell', or None."""
    if vs50 > vs50_buy and vs200 > vs200_buy and (not require_faller or is_faller):
        return "buy"
    if vs50 >= vs50_hold:
        return "hold"
    if vs50 < vs50_sell:
        return "sell"
    return None

def run_simulation(vs50_buy, vs200_buy, vs50_hold, vs50_sell, require_faller):
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

        # entries — only names in ranked_set that get a buy or hold signal
        for sym, ret_3m, price, vs50, vs200 in screener:
            if sym not in ranked_set:
                continue
            if sym in positions:
                continue
            # is_faller approximation: negative day not available historically here,
            # so we treat require_faller as optional extra filter only when True
            # (we skip the faller check in historical sim unless we add daily change)
            signal = passes_candidate(vs50, vs200, False, vs50_buy, vs200_buy,
                                      vs50_hold, vs50_sell, False)
            if signal in ("buy", "hold"):
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

# --- grid ---
results = []
total = len(VS50_BUY) * len(VS200_BUY) * len(VS50_HOLD) * len(VS50_SELL) * len(REQUIRE_FALLER)
n = 0
print(f"Running {total} combinations...\n")

for vs50_buy in VS50_BUY:
    for vs200_buy in VS200_BUY:
        for vs50_hold in VS50_HOLD:
            for vs50_sell in VS50_SELL:
                for require_faller in REQUIRE_FALLER:
                    n += 1
                    print(f"  [{n}/{total}] vs50_buy={vs50_buy} vs200_buy={vs200_buy} "
                          f"vs50_hold={vs50_hold} vs50_sell={vs50_sell} faller={require_faller}...",
                          flush=True)
                    trades = run_simulation(vs50_buy, vs200_buy, vs50_hold, vs50_sell, require_faller)
                    n_trades, win, pnl, roi = summarise(trades)
                    results.append({
                        "vs50_buy": vs50_buy,
                        "vs200_buy": vs200_buy,
                        "vs50_hold": vs50_hold,
                        "vs50_sell": vs50_sell,
                        "faller": require_faller,
                        "trades": n_trades,
                        "win_rate": win,
                        "pnl": pnl,
                        "roi": roi,
                    })

# --- report ---
results.sort(key=lambda x: x["roi"], reverse=True)

print("\n" + "=" * 90)
print(f"{'vs50b':>6} {'vs200b':>7} {'vs50h':>6} {'vs50s':>6} {'Fall':>5} "
      f"{'Trades':>8} {'Win%':>8} {'P&L':>12} {'ROI%':>8}")
print("-" * 90)
for r in results[:30]:  # top 30
    print(f"{r['vs50_buy']:>6} {r['vs200_buy']:>7} {r['vs50_hold']:>6} {r['vs50_sell']:>6} "
          f"{str(r['faller']):>5} {r['trades']:>8} {r['win_rate']:>7.1f}% "
          f"{r['pnl']:>11.2f} {r['roi']:>7.1f}%")
print("=" * 90)

best = results[0]
print(f"\nBest ROI: vs50_buy={best['vs50_buy']} vs200_buy={best['vs200_buy']} "
      f"vs50_hold={best['vs50_hold']} vs50_sell={best['vs50_sell']} faller={best['faller']}")
print(f"  -> {best['roi']:.1f}%  (P&L £{best['pnl']:.2f}, {best['trades']} trades)")
print("\nDone.")