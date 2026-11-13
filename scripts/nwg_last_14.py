# scripts/nwg_last_14.py
# DESC: Show last ~14 daily closes and day-to-day % change for NWG.L
# RUN: Tool2

import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "ape_stock.db"
conn = sqlite3.connect(db_path, timeout=30)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("""
    SELECT date, open, high, low, close, volume
    FROM daily_closes
    WHERE symbol = 'NWG.L'
    ORDER BY date DESC
    LIMIT 15
""")
rows = cur.fetchall()
rows = list(reversed(rows))   # oldest first

if len(rows) < 2:
    print("Not enough NWG.L data")
else:
    print(f"{'Date':<12} {'Close':>10} {'Chg%':>8} {'Volume':>12}")
    print("-" * 46)
    for i, r in enumerate(rows):
        if i == 0:
            chg = ""
        else:
            prev = rows[i-1]["close"]
            if prev:
                chg = f"{(r['close'] - prev) / prev * 100:+.2f}%"
            else:
                chg = ""
        vol = f"{r['volume']:,}" if r["volume"] else ""
        print(f"{r['date']:<12} {r['close']:10.2f} {chg:>8} {vol:>12}")

conn.close()