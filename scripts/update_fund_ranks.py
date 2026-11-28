# scripts/update_fund_ranks.py
# NAME: Update Fund Ranks
# DESC: Calculates pure fundamentals rank (1-351) and stores fund_score / fund_rank.
# DETAIL: Quality (ROE 25%, op margin 20%, rev growth 15%) + Valuation (PE 15%, PB 15%, div yield 10%). Percentile ranks. Safe to re-run. Does not touch base or TA ranks.
# ALLOW_DELETE: 0
# RUN: Tool2
# CATEGORY: scores

"""
Update Fund Ranks
-----------------
Produces a pure fundamentals ranking used as the active rank
when Tool 6 is in Fundamentals mode.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "ape_stock.db"

def percentile_rank(values, higher_is_better=True):
    """Return dict of value -> 0-100 percentile rank. Ties share average rank."""
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
    for col, typ in [("fund_score", "REAL"), ("fund_rank", "INTEGER")]:
        try:
            cur.execute(f"ALTER TABLE stock_scores ADD COLUMN {col} {typ}")
        except sqlite3.OperationalError:
            pass

    # Pull fundamental metrics
    cur.execute("""
        SELECT
            symbol,
            roe,
            operating_margin,
            revenue_growth,
            pe_trailing,
            price_to_book,
            dividend_yield
        FROM fundamentals
        WHERE symbol IS NOT NULL
    """)
    rows = cur.fetchall()
    if not rows:
        print("No fundamentals data.")
        conn.close()
        return

    metrics = {k: [] for k in ["roe", "op_margin", "rev_growth", "pe", "pb", "div"]}
    data = []
    for r in rows:
        item = {
            "symbol": r["symbol"],
            "roe": r["roe"],
            "op_margin": r["operating_margin"],
            "rev_growth": r["revenue_growth"],
            "pe": r["pe_trailing"],
            "pb": r["price_to_book"],
            "div": r["dividend_yield"]
        }
        data.append(item)
        for k in metrics:
            if item[k] is not None:
                metrics[k].append(item[k])

    # Percentile ranks (lower PE / PB better)
    pr = {
        "roe": percentile_rank(metrics["roe"], True),
        "op_margin": percentile_rank(metrics["op_margin"], True),
        "rev_growth": percentile_rank(metrics["rev_growth"], True),
        "pe": percentile_rank(metrics["pe"], False),
        "pb": percentile_rank(metrics["pb"], False),
        "div": percentile_rank(metrics["div"], True)
    }

    def s(item, key):
        v = item[key]
        return pr[key].get(v, 50.0) if v is not None else 50.0

    scored = []
    for item in data:
        fund = (
            s(item, "roe") * 0.25 +
            s(item, "op_margin") * 0.20 +
            s(item, "rev_growth") * 0.15 +
            s(item, "pe") * 0.15 +
            s(item, "pb") * 0.15 +
            s(item, "div") * 0.10
        )
        scored.append((item["symbol"], round(fund, 2)))

    scored.sort(key=lambda x: -x[1])
    rank_map = {sym: i for i, (sym, _) in enumerate(scored, 1)}
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for sym, fund in scored:
        cur.execute("""
            INSERT INTO stock_scores (symbol, score_date, fund_score, fund_rank)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(symbol, score_date) DO UPDATE SET
                fund_score = excluded.fund_score,
                fund_rank = excluded.fund_rank
        """, (sym, today, fund, rank_map[sym]))

    conn.commit()
    conn.close()
    print(f"Fund ranks written for {len(scored)} symbols on {today}.")
    print("Top 10:")
    for i, (sym, sc) in enumerate(scored[:10], 1):
        print(f"  {i:2}. {sym:<8} {sc}")

if __name__ == "__main__":
    main()