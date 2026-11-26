# scripts/dump_stock_scores.py
# NAME: Dump Stock Scores
# DESC: Exports the latest stock_scores rows to the console (and optionally CSV).
# DETAIL: Shows symbol, score_date, base_score, base_rank and any other score columns. Safe read-only.
# ALLOW_DELETE: 0
# RUN: Tool2

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
        return

    cur.execute("""
        SELECT symbol, score_date, base_score, base_rank,
               recovery_score, persistence_score, fundamentals_score, composite_score
        FROM stock_scores
        WHERE score_date = ?
        ORDER BY base_rank ASC
    """, (latest,))

    rows = cur.fetchall()
    print(f"stock_scores for {latest}  ({len(rows)} rows)\n")
    print(f"{'Rank':>4}  {'Symbol':<8}  {'Base':>6}  {'Rec':>6}  {'Pers':>6}  {'Fund':>6}  {'Comp':>6}")
    print("-" * 60)
    for r in rows:
        print(f"{r['base_rank'] or '':>4}  {r['symbol']:<8}  "
              f"{r['base_score'] or 0:>6.1f}  "
              f"{r['recovery_score'] or 0:>6.1f}  "
              f"{r['persistence_score'] or 0:>6.1f}  "
              f"{r['fundamentals_score'] or 0:>6.1f}  "
              f"{r['composite_score'] or 0:>6.1f}")

    conn.close()

if __name__ == "__main__":
    main()