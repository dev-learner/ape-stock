# scripts/create_scores_table.py
# NAME: Create Scores Table
# DESC: Creates the stock_scores table used to store normalised 0-100 scores.
# DETAIL: Safe to re-run. Does not delete existing data.
# ALLOW_DELETE: 0
# RUN: Tool2

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "ape_stock.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
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
    conn.commit()
    conn.close()
    print("stock_scores table ready.")

if __name__ == "__main__":
    main()