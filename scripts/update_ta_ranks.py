# scripts/update_ta_ranks.py
# NAME: Update TA Ranks
# DESC: Calculates pure technical rank (1-351) and stores ta_score / ta_rank.
# DETAIL: 3m 25%, 6m 20%, vs 50MA 20%, vs 200MA 15%, dist 52w 10%, vol 20d 10%. Safe to re-run.
# ALLOW_DELETE: 0
# RUN: Tool2
# CATEGORY: scores

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "ape_stock.db"

def percentile_rank(values, higher_is_better=True):
    clean = [v for v in values if v is not None]
    if not clean:
        return {}
    sorted_vals = sorted(set(clean), reverse=not higher_is_better)
    n = len(sorted_vals)
    return {v: 100.0 * (n - i) / n for i, v in enumerate(sorted_vals)}

def main():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Ensure columns exist
    for col, typ in [("ta_score", "REAL"), ("ta_rank", "INTEGER")]:
        try:
            cur.execute(f"ALTER TABLE stock_scores ADD COLUMN {col} {typ}")
        except sqlite3.OperationalError:
            pass

    cur.execute("""
        SELECT symbol, ret_3m, ret_6m, pct_from_50ma, pct_from_200ma,
               dist_52w_high, vol_20d
        FROM index_quotes
        WHERE symbol IS NOT NULL
    """)
    rows = cur.fetchall()

    metrics = {k: [] for k in ["ret_3m", "ret_6m", "pct_50", "pct_200", "dist", "vol"]}
    data = []
    for r in rows:
        item = {
            "symbol": r["symbol"],
            "ret_3m": r["ret_3m"],
            "ret_6m": r["ret_6m"],
            "pct_50": r["pct_from_50ma"],
            "pct_200": r["pct_from_200ma"],
            "dist": r["dist_52w_high"],
            "vol": r["vol_20d"]
        }
        data.append(item)
        for k in metrics:
            if item[k] is not None:
                metrics[k].append(item[k])

    pr = {
        "ret_3m": percentile_rank(metrics["ret_3m"], True),
        "ret_6m": percentile_rank(metrics["ret_6m"], True),
        "pct_50": percentile_rank(metrics["pct_50"], True),
        "pct_200": percentile_rank(metrics["pct_200"], True),
        "dist": percentile_rank(metrics["dist"], False),
        "vol": percentile_rank(metrics["vol"], False)   # lower vol better for this version
    }

    def s(item, key):
        v = item[key]
        return pr[key].get(v, 50.0) if v is not None else 50.0

    scored = []
    for item in data:
        ta = (s(item, "ret_3m") * 0.25 +
              s(item, "ret_6m") * 0.20 +
              s(item, "pct_50") * 0.20 +
              s(item, "pct_200") * 0.15 +
              s(item, "dist") * 0.10 +
              s(item, "vol") * 0.10)
        scored.append((item["symbol"], round(ta, 2)))

    scored.sort(key=lambda x: -x[1])
    rank_map = {sym: i for i, (sym, _) in enumerate(scored, 1)}
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for sym, ta in scored:
        cur.execute("""
            INSERT INTO stock_scores (symbol, score_date, ta_score, ta_rank)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(symbol, score_date) DO UPDATE SET
                ta_score = excluded.ta_score,
                ta_rank = excluded.ta_rank
        """, (sym, today, ta, rank_map[sym]))

    conn.commit()
    conn.close()
    print(f"TA ranks written for {len(scored)} symbols.")
    print("Top 10:")
    for i, (sym, sc) in enumerate(scored[:10], 1):
        print(f"  {i:2}. {sym:<8} {sc}")

if __name__ == "__main__":
    main()