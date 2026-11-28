# scripts/dump_index_quotes.py
# NAME: Dump Index Quotes
# DESC: Prints every row from the index_quotes table in aligned columns.
# DETAIL: Diagnostic dump of the current quote and screener-metrics snapshot. Read-only.
# ALLOW_DELETE: 1
# RUN: Tool2
# CATEGORY: dumps

"""
Dump Index Quotes
-----------------
Prints the full contents of the index_quotes table as a fixed-width table.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "ape_stock.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM index_quotes ORDER BY symbol")
    rows = cur.fetchall()

    if not rows:
        print("index_quotes is empty")
    else:
        cols = list(rows[0].keys())

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

if __name__ == "__main__":
    main()