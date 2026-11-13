# scripts/hit_grid_search.py
# DESC: Grid-search Hit parameters; report mean, median, trimmed mean + outlier dump
# RUN: Tool2

import sqlite3
from pathlib import Path
from collections import defaultdict
import itertools
import statistics

db_path = Path(__file__).parent.parent / "ape_stock.db"
conn = sqlite3.connect(db_path, timeout=60)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT symbol, market_cap FROM index_quotes WHERE market_cap IS NOT NULL")
mkt_caps = {r["symbol"]: r["market_cap"] for r in cur.fetchall()}

cur.execute("""
    SELECT symbol, date, close, volume
    FROM daily_closes
    WHERE close IS NOT NULL AND volume IS NOT NULL
    ORDER BY symbol, date
""")
rows = cur.fetchall()

by_sym = defaultdict(list)
for r in rows:
    by_sym[r["symbol"]].append(dict(r))

def calc_rsi(closes, period=7):
    if len(closes) < period + 1:
        return None
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [max(d, 0) for d in deltas]
    losses = [max(-d, 0) for d in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def trimmed_mean(vals, prop=0.05):
    if len(vals) < 20:
        return statistics.mean(vals) if vals else 0.0
    s = sorted(vals)
    k = int(len(s) * prop)
    return statistics.mean(s[k:-k]) if k else statistics.mean(s)

print("Pre-computing daily features...")
features = []
for sym, data in by_sym.items():
    if len(data) < 50:
        continue
    closes = [d["close"] for d in data]
    vols = [d["volume"] for d in data]
    mkt = mkt_caps.get(sym, 0)
    for i in range(35, len(data) - 14):
        prev_c = data[i-1]["close"]
        if not prev_c or prev_c == 0:
            continue
        chg_pct = (data[i]["close"] - prev_c) / prev_c * 100
        if chg_pct >= 0:
            continue
        window = vols[max(0, i-30):i]
        avg_vol = sum(window) / len(window) if window else 0
        vol_ratio = data[i]["volume"] / avg_vol if avg_vol else 0
        rsi = calc_rsi(closes[max(0, i-40):i+1])
        imp = abs(mkt * chg_pct / 100) if mkt else 0
        nets = {}
        for fwd in (5, 10):
            if i + fwd < len(data):
                future = data[i + fwd]["close"]
                if future:
                    nets[fwd] = ((future - data[i]["close"]) / data[i]["close"] - 0.005) * 100
        features.append({
            "sym": sym,
            "date": data[i]["date"],
            "chg": chg_pct,
            "vol": vol_ratio,
            "rsi": rsi,
            "imp": imp,
            "nets": nets,
            "close": data[i]["close"]
        })

print(f"Feature rows: {len(features)}")

CHG_PCTS = [5, 6, 7]
VOL_RATIOS = [1.5, 2.0, None]
RSI_LEVELS = [30, None]
HIT_REQS = [50, 75, 100]
IMPACT_LEVELS = [None, 20_000_000]
FORWARDS = [5, 10]

results = []
best_trades = []          # keep the actual trades of the eventual winner
combos = list(itertools.product(CHG_PCTS, VOL_RATIOS, RSI_LEVELS, HIT_REQS, IMPACT_LEVELS))
print(f"Testing {len(combos)} parameter sets...")

for idx, (chg, vol_r, rsi_l, hit_req, impact) in enumerate(combos):
    if idx % 20 == 0:
        print(f"  {idx}/{len(combos)}", flush=True)
    for fwd in FORWARDS:
        hit_rets = []
        hit_trades = []
        ctrl_rets = []
        for f in features:
            net = f["nets"].get(fwd)
            if net is None:
                continue
            if f["chg"] <= -5:
                ctrl_rets.append(net)

            points = 0
            possible = 0
            possible += 1
            if abs(f["chg"]) >= chg:
                points += 1
            if vol_r is not None:
                possible += 1
                if f["vol"] >= vol_r:
                    points += 1
            if rsi_l is not None:
                possible += 1
                if f["chg"] <= -chg and f["rsi"] is not None and f["rsi"] <= rsi_l:
                    points += 1
            if impact is not None:
                possible += 1
                if f["imp"] >= impact:
                    points += 1
            if possible and (points / possible * 100) >= hit_req:
                hit_rets.append(net)
                hit_trades.append((f["sym"], f["date"], f["chg"], net, f["close"]))

        if len(hit_rets) < 30:
            continue
        h_avg = statistics.mean(hit_rets)
        h_med = statistics.median(hit_rets)
        h_trim = trimmed_mean(hit_rets)
        h_win = sum(1 for r in hit_rets if r > 0) / len(hit_rets) * 100
        c_avg = statistics.mean(ctrl_rets) if ctrl_rets else 0
        edge = h_avg - c_avg
        results.append({
            "fwd": fwd, "chg": chg,
            "vol": vol_r if vol_r else "off",
            "rsi": rsi_l if rsi_l else "off",
            "hit": hit_req,
            "imp": "20m" if impact else "off",
            "n": len(hit_rets),
            "avg": h_avg, "med": h_med, "trim": h_trim,
            "win": h_win, "c_avg": c_avg, "edge": edge,
            "trades": hit_trades
        })

results.sort(key=lambda x: (x["edge"], x["avg"]), reverse=True)

print(f"\nTop 15 parameter sets (ranked by mean edge)\n")
print(f"{'Fwd':>3} {'Chg':>3} {'Vol':>5} {'RSI':>4} {'Hit':>3} {'Imp':>4} "
      f"{'N':>5} {'Mean':>7} {'Med':>7} {'Trim':>7} {'Win%':>6} {'Ctrl':>7} {'Edge':>7}")
print("-" * 85)
for r in results[:15]:
    print(f"{r['fwd']:3} {r['chg']:3} {str(r['vol']):>5} {str(r['rsi']):>4} {r['hit']:3} {r['imp']:>4} "
          f"{r['n']:5} {r['avg']:7.2f} {r['med']:7.2f} {r['trim']:7.2f} {r['win']:6.1f} "
          f"{r['c_avg']:7.2f} {r['edge']:7.2f}")

# Outlier dump for the single best set
if results:
    best = results[0]
    trades = sorted(best["trades"], key=lambda t: t[3], reverse=True)
    print(f"\n=== Outlier dump for best set ===")
    print(f"Fwd={best['fwd']} Chg>={best['chg']} Vol={best['vol']} RSI={best['rsi']} "
          f"Hit>={best['hit']} Imp={best['imp']}  N={best['n']}")
    print("\nTop 8 winners:")
    print(f"{'Symbol':<10} {'Date':<12} {'Fall%':>7} {'Net%':>8} {'Close':>8}")
    for t in trades[:8]:
        print(f"{t[0]:<10} {t[1]:<12} {t[2]:7.1f} {t[3]:8.1f} {t[4]:8.2f}")
    print("\nBottom 8 losers:")
    for t in trades[-8:]:
        print(f"{t[0]:<10} {t[1]:<12} {t[2]:7.1f} {t[3]:8.1f} {t[4]:8.2f}")

print(f"\nTotal result rows: {len(results)}")
conn.close()