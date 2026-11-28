# scripts/hit_backtest.py
# NAME: Hit Score Back-test
# DESC: Back-tests the current Hit rules and compares forward returns against a simple control.
# DETAIL: Applies the four-point Hit scoring rules to every historical day in daily_closes and measures the subsequent net return (after stamp) over 1, 3, 5, 10 and 14 days. Only fallers that meet the Hit threshold are counted as signals. Uses current market cap as a proxy for the £-impact rule. Read-only.
# ALLOW_DELETE: 1
# RUN: Tool2
# CATEGORY: analysis

"""
Hit Score Back-test
-------------------
Tests whether the current Hit scoring rules have historically identified
short-term bounce opportunities.

For each day the script calculates the four Hit points (large move, £ impact,
volume spike, oversold RSI on a faller). Days that score at or above the
threshold and are fallers are treated as signals. Forward net returns
(after 0.5 % stamp) are then measured and compared with a naïve control
of all large fallers.
"""

import sqlite3
from pathlib import Path
from collections import defaultdict

DB_PATH = Path(__file__).parent.parent / "ape_stock.db"

def calc_rsi(closes, period=7):
    """Simple RSI calculation."""
    if len(closes) < period + 1:
        return None
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def main():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT symbol, market_cap FROM index_quotes WHERE market_cap IS NOT NULL")
    mkt_caps = {r["symbol"]: r["market_cap"] for r in cur.fetchall()}

    cur.execute("""
        SELECT symbol, date, open, high, low, close, volume
        FROM daily_closes
        WHERE close IS NOT NULL AND volume IS NOT NULL
        ORDER BY symbol, date
    """)
    rows = cur.fetchall()

    by_sym = defaultdict(list)
    for r in rows:
        by_sym[r["symbol"]].append(dict(r))

    STAMP = 0.005
    HIT_THRESHOLD = 50
    FORWARD_DAYS = [1, 3, 5, 10, 14]
    VOL_RATIO = 1.5
    FALL_PCT = 5.0

    print(f"Hit back-test  |  threshold >= {HIT_THRESHOLD}%  |  stamp {STAMP*100:.1f}%")
    print(f"{'Fwd':>4} {'Signals':>8} {'AvgNet%':>9} {'Win%':>7} {'CtrlSig':>8} {'CtrlNet%':>9} {'CtrlWin%':>8}")
    print("-" * 70)

    for fwd in FORWARD_DAYS:
        hit_rets = []
        ctrl_rets = []

        for sym, data in by_sym.items():
            if len(data) < 40:
                continue
            closes = [d["close"] for d in data]
            vols = [d["volume"] for d in data]

            for i in range(30, len(data) - fwd):
                prev_c = data[i-1]["close"]
                if not prev_c:
                    continue
                chg_pct = (data[i]["close"] - prev_c) / prev_c * 100

                window = vols[i-30:i]
                avg_vol = sum(window) / len(window) if window else 0
                vol_ratio = data[i]["volume"] / avg_vol if avg_vol else 0

                rsi = calc_rsi(closes[max(0, i-30):i+1])

                mkt = mkt_caps.get(sym, 0)
                impact = abs(mkt * chg_pct / 100) if mkt else 0

                points = 0
                if abs(chg_pct) >= 5:
                    points += 1
                if impact >= 20_000_000:
                    points += 1
                if vol_ratio >= VOL_RATIO:
                    points += 1
                if chg_pct <= -FALL_PCT and rsi is not None and rsi <= 30:
                    points += 1

                hit_pct = (points / 4) * 100

                future_c = data[i + fwd]["close"]
                if not future_c:
                    continue
                gross = (future_c - data[i]["close"]) / data[i]["close"]
                net = gross - STAMP

                if hit_pct >= HIT_THRESHOLD and chg_pct < 0:
                    hit_rets.append(net * 100)
                if chg_pct <= -FALL_PCT:
                    ctrl_rets.append(net * 100)

        def stats(rets):
            if not rets:
                return 0, 0.0, 0.0
            avg = sum(rets) / len(rets)
            wins = sum(1 for r in rets if r > 0) / len(rets) * 100
            return len(rets), avg, wins

        h_n, h_avg, h_win = stats(hit_rets)
        c_n, c_avg, c_win = stats(ctrl_rets)

        print(f"{fwd:4} {h_n:8} {h_avg:9.2f} {h_win:7.1f} {c_n:8} {c_avg:9.2f} {c_win:8.1f}")

    conn.close()
    print("\nNote: £ impact uses current market_cap as proxy. Fallers only for Hit cohort.")

if __name__ == "__main__":
    main()