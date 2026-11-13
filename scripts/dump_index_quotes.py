# dump_index_quotes.py
# DESC: Dump all index_quotes rows in aligned columns
# RUN: Tool2

import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "ape_stock.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT * FROM index_quotes ORDER BY symbol")
rows = cur.fetchall()

if not rows:
    print("index_quotes is empty")
else:
    cols = list(rows[0].keys())

    # Build formatted rows
    formatted = []
    for r in rows:
        line = []
        for c in cols:
            val = r[c]
            if isinstance(val, float):
                line.append(f"{val:.4f}")
            elif val is None:
                line.append("")
            else:
                line.append(str(val))
        formatted.append(line)

    # Calculate column widths
    widths = [len(c) for c in cols]
    for line in formatted:
        for i, cell in enumerate(line):
            widths[i] = max(widths[i], len(cell))

    # Print header
    header = "  ".join(c.ljust(widths[i]) for i, c in enumerate(cols))
    print(header)
    print("-" * len(header))

    # Print rows
    for line in formatted:
        print("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(line)))

print(f"\nTotal rows: {len(rows)}")
conn.close()