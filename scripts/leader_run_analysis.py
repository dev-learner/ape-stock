# scripts/leader_run_analysis.py
# NAME: Leader Run Analysis
# DESC: Analyses when current Screener leaders started their sustained runs and compares entry vs current metrics.
# DETAIL: Takes the current top 30 from daily_ranks. For each stock identifies the start of the current sustained leadership phase (first close above the 50-day MA that was followed by at least 10 consecutive closes still above the 50-day). Records technical metrics at that start date and today, plus estimated market cap then vs current market cap. Read-only.
# ALLOW_DELETE: 1
# RUN: Tool2
# CATEGORY: analysis

"""
Leader Run Analysis
-------------------
For the current Tool 4 leaders (top 30):

1. Finds the start of the current sustained run
   (>=10 consecutive closes above the 50-day MA).
2. Records key technical metrics on that start date and today.
3. Estimates market cap at the start (start price in pounds × latest shares)
   and shows current market cap.
"""

import sqlite3
from pathlib import Path
from collections import defaultdict

DB_PATH = Path(__file__).parent.parent / "ape_stock.db"
TOP_N = 30
MIN_SUSTAINED_DAYS = 10

def main():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT MAX(date) FROM daily_ranks")
    latest = cur.fetchone()[0]
    if not latest:
        print("No ranks available.")
        return

    cur.execute("""
        SELECT symbol, rank, score
        FROM daily_ranks
        WHERE date = ?
        ORDER BY rank
        LIMIT ?
    """, (latest, TOP_N))
    leaders = cur.fetchall()
    print(f"Analysing top {len(leaders)} leaders as of {latest}")
    print(f"Sustained-run definition: >={MIN_SUSTAINED_DAYS} consecutive closes above 50-day MA\n")

    cur.execute("""
        SELECT symbol, date, close
        FROM daily_closes
        WHERE close IS NOT NULL
        ORDER BY symbol, date
    """)
    by_sym = defaultdict(list)
    for r in cur.fetchall():
        by_sym[r["symbol"]].append((r["date"], float(r["close"])))

    results = []

    for lead in leaders:
        sym = lead["symbol"]
        series = by_sym.get(sym, [])
        if len(series) < 200:
            continue

        dates = [d for d, c in series]
        closes = [c for d, c in series]
        n = len(closes)

        above_50 = []
        for i in range(n):
            if i < 49:
                above_50.append(False)
                continue
            ma50 = sum(closes[i-49:i+1]) / 50
            above_50.append(closes[i] > ma50)

        start_idx = None
        if above_50[-1]:
            streak = 0
            for i in range(n-1, -1, -1):
                if above_50[i]:
                    streak += 1
                else:
                    break
            if streak >= MIN_SUSTAINED_DAYS:
                start_idx = n - streak

        if start_idx is None:
            continue

        start_date = dates[start_idx]
        start_close = closes[start_idx]
        today_close = closes[-1]
        days_in_run = n - 1 - start_idx

        def metrics_at(idx):
            c = closes[idx]
            ma50 = sum(closes[max(0, idx-49):idx+1]) / min(50, idx+1)
            ma200 = sum(closes[max(0, idx-199):idx+1]) / min(200, idx+1)
            ret3 = (c / closes[idx-63] - 1) * 100 if idx >= 63 else None
            ret6 = (c / closes[idx-126] - 1) * 100 if idx >= 126 else None
            lookback = min(252, idx+1)
            high52 = max(closes[idx-lookback+1:idx+1])
            dist_high = (c / high52 - 1) * 100 if high52 else None
            return {
                "pct_50": (c / ma50 - 1) * 100 if ma50 else None,
                "pct_200": (c / ma200 - 1) * 100 if ma200 else None,
                "ret3": ret3,
                "ret6": ret6,
                "dist_high": dist_high
            }

        start_m = metrics_at(start_idx)
        now_m = metrics_at(n-1)

        cur.execute("""
            SELECT shares_outstanding
            FROM fundamentals
            WHERE symbol = ? AND shares_outstanding IS NOT NULL
        """, (sym,))
        shares_row = cur.fetchone()
        shares = shares_row["shares_outstanding"] if shares_row else None

        # Price is in pence → convert to pounds
        mcap_start_est = (start_close / 100 * shares) if shares else None

        cur.execute("""
            SELECT market_cap
            FROM fundamentals
            WHERE symbol = ?
        """, (sym,))
        mcap_row = cur.fetchone()
        mcap_now = mcap_row["market_cap"] if mcap_row else None

        results.append({
            "symbol": sym,
            "rank": lead["rank"],
            "days": days_in_run,
            "start_date": start_date,
            "price_change": (today_close / start_close - 1) * 100,
            "start_m": start_m,
            "now_m": now_m,
            "mcap_start": mcap_start_est,
            "mcap_now": mcap_now
        })

    def fmt_mcap(v):
        if not v:
            return "       -"
        if v >= 1_000_000_000:
            return f"{v/1_000_000_000:9.1f}B"
        return f"{v/1_000_000:9.0f}M"

    print(f"{'Symbol':<8} {'Rank':>4} {'Days':>5} {'Start':<12} {'PxChg%':>7} "
          f"{'St%50':>6} {'Now%50':>6} {'StMcap':>10} {'NowMcap':>10}")
    print("-" * 80)
    for r in sorted(results, key=lambda x: x["rank"]):
        print(f"{r['symbol']:<8} {r['rank']:4} {r['days']:5} {r['start_date']:<12} "
              f"{r['price_change']:7.1f} "
              f"{(r['start_m']['pct_50'] or 0):6.1f} {(r['now_m']['pct_50'] or 0):6.1f} "
              f"{fmt_mcap(r['mcap_start']):>10} {fmt_mcap(r['mcap_now']):>10}")

    conn.close()
    print("\nDone.")

if __name__ == "__main__":
    main()