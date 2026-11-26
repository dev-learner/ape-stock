# scripts/update_base_ranks.py
# NAME: Update Base Ranks
# DESC: Calculates the balanced base score and global rank (1-351) for every symbol.
# DETAIL: Momentum/Trend 40%, Quality 30%, Valuation 20%, Liquidity & Risk 10%. Writes base_score and base_rank to stock_scores for today's date. Safe to re-run. Does not touch daily_ranks.
# ALLOW_DELETE: 1
# RUN: Tool2

"""
Update Base Ranks
-----------------
Produces the single balanced global ranking used as the default order
in Tool 4 and Tool 6.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

DB_PATH = Path(__file__).parent.parent / "ape_stock.db"

def percentile_rank(values, higher_is_better=True):
    """Return dict of value -> 0-100 percentile rank."""
    clean = [v for v in values if v is not None]
    if not clean:
        return {}
    sorted_vals = sorted(clean, reverse=not higher_is_better)
    n = len(sorted_vals)
    ranks = {}
    for i, v in enumerate(sorted_vals):
        # average rank for ties
        ranks[v] = ranks.get(v, 100.0 * (n - i) / n)
    return ranks

def main():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Ensure table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_scores (
            symbol TEXT,
            score_date TEXT,
            recovery_score REAL,
            persistence_score REAL,
            fundamentals_score REAL,
            composite_score REAL,
            base_score REAL,
            base_rank INTEGER,
            PRIMARY KEY (symbol, score_date)
        )
    """)

    # Pull required fields
    cur.execute("""
        SELECT
            q.symbol,
            q.ret_3m,
            q.ret_6m,
            q.pct_from_50ma,
            q.pct_from_200ma,
            q.dist_52w_high,
            q.market_cap,
            q.avg_volume,
            q.price,
            f.roe,
            f.operating_margin,
            f.revenue_growth,
            f.pe_trailing,
            f.price_to_book
        FROM index_quotes q
        LEFT JOIN fundamentals f ON f.symbol = q.symbol
        WHERE q.symbol IS NOT NULL
    """)
    rows = cur.fetchall()
    if not rows:
        print("No data.")
        conn.close()
        return

    # Collect metric lists
    metrics = {
        "ret_3m": [],
        "ret_6m": [],
        "pct_50": [],
        "pct_200": [],
        "roe": [],
        "op_margin": [],
        "rev_growth": [],
        "pe": [],
        "pb": [],
        "adv": [],          # average daily value
        "dist_high": []
    }

    data = []
    for r in rows:
        adv = None
        if r["price"] and r["avg_volume"]:
            adv = (r["price"] / 100.0) * r["avg_volume"]   # pence → pounds

        item = {
            "symbol": r["symbol"],
            "ret_3m": r["ret_3m"],
            "ret_6m": r["ret_6m"],
            "pct_50": r["pct_from_50ma"],
            "pct_200": r["pct_from_200ma"],
            "roe": r["roe"],
            "op_margin": r["operating_margin"],
            "rev_growth": r["revenue_growth"],
            "pe": r["pe_trailing"],
            "pb": r["price_to_book"],
            "adv": adv,
            "dist_high": r["dist_52w_high"]
        }
        data.append(item)
        for k in metrics:
            if item[k] is not None:
                metrics[k].append(item[k])

    # Percentile ranks
    pr = {
        "ret_3m": percentile_rank(metrics["ret_3m"], True),
        "ret_6m": percentile_rank(metrics["ret_6m"], True),
        "pct_50": percentile_rank(metrics["pct_50"], True),
        "pct_200": percentile_rank(metrics["pct_200"], True),
        "roe": percentile_rank(metrics["roe"], True),
        "op_margin": percentile_rank(metrics["op_margin"], True),
        "rev_growth": percentile_rank(metrics["rev_growth"], True),
        "pe": percentile_rank(metrics["pe"], False),          # lower PE better (simple)
        "pb": percentile_rank(metrics["pb"], False),
        "adv": percentile_rank(metrics["adv"], True),
        "dist_high": percentile_rank(metrics["dist_high"], False)  # closer to high better
    }

    def score_of(item, key):
        v = item[key]
        return pr[key].get(v, 50.0) if v is not None else 50.0

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    scored = []

    for item in data:
        mom = (score_of(item, "ret_3m") + score_of(item, "ret_6m") +
               score_of(item, "pct_50") + score_of(item, "pct_200")) / 4.0
        qual = (score_of(item, "roe") + score_of(item, "op_margin") +
                score_of(item, "rev_growth")) / 3.0
        val = (score_of(item, "pe") + score_of(item, "pb")) / 2.0
        liq = (score_of(item, "adv") + score_of(item, "dist_high")) / 2.0

        base = (mom * 0.40) + (qual * 0.30) + (val * 0.20) + (liq * 0.10)
        scored.append((item["symbol"], round(base, 2)))

    # Rank
    scored.sort(key=lambda x: -x[1])
    rank_map = {sym: i for i, (sym, _) in enumerate(scored, 1)}

    # Write
    for sym, base in scored:
        cur.execute("""
            INSERT INTO stock_scores (symbol, score_date, base_score, base_rank)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(symbol, score_date) DO UPDATE SET
                base_score = excluded.base_score,
                base_rank = excluded.base_rank
        """, (sym, today, base, rank_map[sym]))

    conn.commit()
    conn.close()
    print(f"Base ranks written for {len(scored)} symbols on {today}.")
    print("Top 10:")
    for i, (sym, sc) in enumerate(scored[:10], 1):
        print(f"  {i:2}. {sym:<8} {sc}")

if __name__ == "__main__":
    main()