# scripts/dump_fundamentals.py
# DESC: Dump all rows from the fundamentals table in aligned columns
# RUN: Tool2

import sqlite3
from pathlib import Path

print("Script started", flush=True)

db_path = Path(__file__).parent.parent / "ape_stock.db"
conn = sqlite3.connect(db_path, timeout=20)
print("Connected", flush=True)

conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("PRAGMA table_info(fundamentals)")
cols = [r[1] for r in cur.fetchall()]
print("Columns:", cols)

cur.execute(f"SELECT {', '.join(cols)} FROM fundamentals ORDER BY symbol")
rows = cur.fetchall()

if not rows:
    print("fundamentals table is empty")
else:
    formatted = []
    for r in rows:
        line = []
        for c in cols:
            val = r[c]
            if isinstance(val, float):
                line.append(f"{val:.4f}")
            else:
                line.append(str(val) if val is not None else "")
        formatted.append(line)

    widths = [len(c) for c in cols]
    for line in formatted:
        for i, cell in enumerate(line):
            widths[i] = max(widths[i], len(cell))

    header = "  ".join(c.ljust(widths[i]) for i, c in enumerate(cols))
    print(header)
    print("-" * len(header))

    for line in formatted:
        print("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(line)))

print(f"\nTotal rows: {len(rows)}")
conn.close()