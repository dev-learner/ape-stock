# quick_faller_volume.py
# DESC: List current fallers ≤ –5 % and flag those with volume > average
# RUN: Tool2

import sqlite3
import os
from pathlib import Path

db_path = Path(__file__).parent.parent / "ape_stock.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Adjust the fall threshold here
FALL_PCT = -5.0

cur.execute("""
    SELECT symbol, name, price, change_pct, volume, avg_volume
    FROM index_quotes
    WHERE change_pct <= ?
      AND avg_volume IS NOT NULL
      AND avg_volume > 0
    ORDER BY change_pct ASC
""", (FALL_PCT,))

rows = cur.fetchall()
print(f"Fallers <= {FALL_PCT}% : {len(rows)}")
print("-" * 70)

high_vol = 0
for r in rows:
    flag = "HIGH VOL" if r["volume"] > r["avg_volume"] else ""
    if flag:
        high_vol += 1
    print(f"{r['symbol']:<10} {r['change_pct']:>7.2f}%  "
          f"vol {r['volume']:>12,}  avg {r['avg_volume']:>12,}  {flag}")

print("-" * 70)
print(f"Of which volume > average volume: {high_vol}")
if rows:
    print(f"Percentage: {high_vol / len(rows) * 100:.1f}%")

conn.close()