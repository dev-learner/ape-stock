# check_avg_volume.py
# DESC: Check how many index_quotes rows have avg_volume populated
# RUN: Tool2

import sqlite3
import os
from pathlib import Path

db_path = Path(__file__).parent.parent / "ape_stock.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM index_quotes")
total = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM index_quotes WHERE avg_volume IS NOT NULL AND avg_volume > 0")
filled = cur.fetchone()[0]

print(f"Total rows: {total}")
print(f"Rows with avg_volume > 0: {filled}")

cur.execute("SELECT symbol, volume, avg_volume FROM index_quotes LIMIT 10")
for r in cur.fetchall():
    print(r)

conn.close()