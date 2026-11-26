# scripts/add_base_columns.py
# NAME: Add Base Columns
# DESC: Adds base_score and base_rank columns to stock_scores if they are missing.
# ALLOW_DELETE: 0
# RUN: Tool2

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "ape_stock.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for col, typ in [("base_score", "REAL"), ("base_rank", "INTEGER")]:
        try:
            cur.execute(f"ALTER TABLE stock_scores ADD COLUMN {col} {typ}")
            print(f"Added {col}")
        except sqlite3.OperationalError:
            print(f"{col} already exists")
    conn.commit()
    conn.close()
    print("Done.")

if __name__ == "__main__":
    main()