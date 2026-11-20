# scripts/dump_external_constituents.py
# DESC: Dump external_constituents table
# RUN: Tool2

import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "ape_stock.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT * FROM external_constituents ORDER BY market, symbol")
rows = cur.fetchall()

if not rows:
    print("No rows in external_constituents.")
else:
    print(f"{'Symbol':<12} {'Market':<10} {'Name':<40} Updated")
    print("-" * 80)
    for r in rows:
        print(f"{r['symbol']:<12} {r['market']:<10} {(r['name'] or '')[:38]:<40} {r['updated'] or ''}")

print(f"\nTotal: {len(rows)}")
conn.close()