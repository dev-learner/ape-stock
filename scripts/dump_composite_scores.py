# scripts/dump_composite_scores.py
# NAME: Dump Composite Scores
# DESC: Exports the latest composite scores and ranks to the console.
# DETAIL: Shows symbol, composite_score, composite_rank plus the component scores. Read-only. Safe.
# ALLOW_DELETE: 0
# RUN: Tool2

"""
Dump Composite Scores
---------------------
Prints the latest composite ranking for inspection.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "ape_stock.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT MAX(score_date) FROM stock_scores")
    latest = cur.fetchone()[0]
    if not latest:
        print("No scores found.")
        conn.close()
        return

    cur.execute("""
        SELECT
            symbol,
            score_date,
            base_score,
            ta_score,
            fund_score,
            composite_score,
            composite_rank
        FROM stock_scores
        WHERE score_date = ?
          AND composite_rank IS NOT NULL
        ORDER BY composite_rank ASC
    """, (latest,))

    rows = cur.fetchall()
    print(f"Composite scores for {latest} ({len(rows)} rows)\n")
    print(f"{'Rank':>4} {'Symbol':<8} {'Base':>6} {'TA':>6} {'Fund':>6} {'Comp':>6}")
    print("-" * 50)
    for r in rows:
        print(f"{r['composite_rank'] or '':>4} {r['symbol']:<8} "
              f"{r['base_score'] or 0:>6.1f} "
              f"{r['ta_score'] or 0:>6.1f} "
              f"{r['fund_score'] or 0:>6.1f} "
              f"{r['composite_score'] or 0:>6.1f}")

    conn.close()

if __name__ == "__main__":
    main()