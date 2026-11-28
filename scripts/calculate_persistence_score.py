# scripts/calculate_persistence_score.py
# NAME: Calculate Persistence Score
# DESC: Computes a 0-100 Persistence score from the latest daily_ranks.
# DETAIL: Converts rank into a percentile-style score (1 = 100). Safe to re-run.
# ALLOW_DELETE: 0
# RUN: Tool2
# CATEGORY: scores

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "ape_stock.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT MAX(date) FROM daily_ranks")
    latest = cur.fetchone()[0]
    if not latest:
        print("No ranks found.")
        return

    cur.execute("SELECT symbol, rank FROM daily_ranks WHERE date = ?", (latest,))
    rows = cur.fetchall()
    if not rows:
        print("No rank rows.")
        return

    max_rank = max(r["rank"] for r in rows if r["rank"] is not None)

    def to_score(rank):
        if rank is None or max_rank == 0:
            return None
        # rank 1 → 100, worst rank → near 0
        return round(100.0 * (max_rank - rank + 1) / max_rank, 1)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    count = 0
    for r in rows:
        score = to_score(r["rank"])
        cur.execute("""
            INSERT INTO stock_scores (symbol, score_date, persistence_score)
            VALUES (?, ?, ?)
            ON CONFLICT(symbol, score_date) DO UPDATE SET persistence_score = excluded.persistence_score
        """, (r["symbol"], today, score))
        count += 1

    conn.commit()
    conn.close()
    print(f"Persistence scores written for {count} symbols (date {latest}).")

if __name__ == "__main__":
    main()