# scripts/calculate_recovery_score.py
# NAME: Calculate Recovery Score
# DESC: Computes a 0-100 Recovery score for every symbol and stores it.
# DETAIL: Score is based on bounce strength relative to the current Recovery Screen universe. Simple percentile-style for now. Safe to re-run.
# ALLOW_DELETE: 1
# RUN: Tool2

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "ape_stock.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Ensure table exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_scores (
            symbol TEXT,
            score_date TEXT,
            recovery_score REAL,
            persistence_score REAL,
            fundamentals_score REAL,
            composite_score REAL,
            PRIMARY KEY (symbol, score_date)
        )
    """)

    # Pull latest recovery candidates (bounce_pct)
    # For a first version we score only names that appear in the recovery logic.
    # Non-candidates receive NULL / 0.
    cur.execute("""
        SELECT symbol, bounce_pct
        FROM (
            -- placeholder: in practice call the same logic as /screens/recovery
            -- or read from a temporary result. For now we demonstrate the pattern.
            SELECT symbol, 0 AS bounce_pct FROM index_quotes WHERE 1=0
        )
    """)
    # NOTE: Replace the above query with real recovery data when wiring.
    # Example real approach: import or duplicate the recovery selection and collect bounce_pct.

    rows = cur.fetchall()
    if not rows:
        print("No recovery data available yet — wire to recovery logic.")
        conn.close()
        return

    # Simple 0-100 scaling by percentile of bounce
    bounces = sorted([r["bounce_pct"] for r in rows if r["bounce_pct"] is not None])
    def to_score(val):
        if val is None or not bounces:
            return None
        rank = sum(1 for b in bounces if b <= val)
        return round(100.0 * rank / len(bounces), 1)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    count = 0
    for r in rows:
        score = to_score(r["bounce_pct"])
        cur.execute("""
            INSERT OR REPLACE INTO stock_scores (symbol, score_date, recovery_score)
            VALUES (?, ?, ?)
        """, (r["symbol"], today, score))
        count += 1

    conn.commit()
    conn.close()
    print(f"Recovery scores written for {count} symbols.")

if __name__ == "__main__":
    main()