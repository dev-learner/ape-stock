# scripts/update_composite_score.py
# NAME: Update Composite Score
# DESC: Calculates weighted composite score and rank from Base, TA and Fundamentals scores.
# DETAIL: Reads weight_base, weight_ta, weight_fund from app_settings (defaults 40/30/30). Writes composite_score and composite_rank. Safe to re-run.
# ALLOW_DELETE: 1
# RUN: Tool2

"""
Update Composite Score
----------------------
Produces the final weighted score used for Tool 12 ordering.
Weights are read from Settings.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "ape_stock.db"

def get_weight(cur, key, default):
    """Read a weight from app_settings, falling back to default."""
    cur.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
    row = cur.fetchone()
    if row and row[0] is not None:
        try:
            return float(row[0])
        except (TypeError, ValueError):
            pass
    return float(default)

def main():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Ensure composite columns exist
    for col, typ in [("composite_score", "REAL"), ("composite_rank", "INTEGER")]:
        try:
            cur.execute(f"ALTER TABLE stock_scores ADD COLUMN {col} {typ}")
        except sqlite3.OperationalError:
            pass

    # Read weights (normalise so they sum to 1.0)
    w_base = get_weight(cur, "weight_base", 40)
    w_ta = get_weight(cur, "weight_ta", 30)
    w_fund = get_weight(cur, "weight_fund", 30)
    total = w_base + w_ta + w_fund
    if total <= 0:
        w_base, w_ta, w_fund = 40, 30, 30
        total = 100
    w_base /= total
    w_ta /= total
    w_fund /= total

    print(f"Weights: Base {w_base*100:.1f}%  TA {w_ta*100:.1f}%  Fund {w_fund*100:.1f}%")

    # Latest scores
    cur.execute("""
        SELECT symbol, base_score, ta_score, fund_score
        FROM stock_scores
        WHERE score_date = (SELECT MAX(score_date) FROM stock_scores)
          AND symbol IS NOT NULL
    """)
    rows = cur.fetchall()
    if not rows:
        print("No scores available.")
        conn.close()
        return

    scored = []
    for r in rows:
        base = r["base_score"] if r["base_score"] is not None else 50.0
        ta = r["ta_score"] if r["ta_score"] is not None else 50.0
        fund = r["fund_score"] if r["fund_score"] is not None else 50.0
        composite = (base * w_base) + (ta * w_ta) + (fund * w_fund)
        scored.append((r["symbol"], round(composite, 2)))

    scored.sort(key=lambda x: -x[1])
    rank_map = {sym: i for i, (sym, _) in enumerate(scored, 1)}
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    for sym, comp in scored:
        cur.execute("""
            INSERT INTO stock_scores (symbol, score_date, composite_score, composite_rank)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(symbol, score_date) DO UPDATE SET
                composite_score = excluded.composite_score,
                composite_rank = excluded.composite_rank
        """, (sym, today, comp, rank_map[sym]))

    conn.commit()
    conn.close()
    print(f"Composite scores written for {len(scored)} symbols on {today}.")
    print("Top 10:")
    for i, (sym, sc) in enumerate(scored[:10], 1):
        print(f"  {i:2}. {sym:<8} {sc}")

if __name__ == "__main__":
    main()