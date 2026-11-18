# scripts/drop_portfolio_tables.py
# DESC: Drop portfolio tables so they can be recreated cleanly
# RUN: Tool2

import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "ape_stock.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

print("Dropping portfolio tables...")

cur.execute("DROP TABLE IF EXISTS portfolio_transactions")
cur.execute("DROP TABLE IF EXISTS portfolio_positions")
cur.execute("DELETE FROM sqlite_sequence WHERE name = 'portfolio_transactions'")

conn.commit()
conn.close()

print("Done. Restart the app to recreate the tables with the latest schema.")