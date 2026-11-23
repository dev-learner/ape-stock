# scripts/dump_daily_closes.py
# NAME: Dump Daily Closes
# DESC: Prints every row from the daily_closes table in aligned columns.
# DETAIL: Diagnostic dump of the entire daily_closes table. Useful for inspecting raw price history. Read-only.
# ALLOW_DELETE: 1
# RUN: Tool2

"""
Dump Daily Closes
-----------------
Prints the full contents of the daily_closes table as a fixed-width table.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "ape_stock.db"

def main():
    print("Script started", flush=True)
    conn = sqlite3.connect(DB_PATH, timeout=20)
    print("Connected", flush=True)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(daily_closes)")
    cols = [r[1] for r in cur.fetchall()]
    print("Columns:", cols)

    cur.execute(f"SELECT {', '.join(cols)} FROM daily_closes ORDER BY symbol, date")
    rows = cur.fetchall()

    if not rows:
        print("daily_closes is empty")
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

if __name__ == "__main__":
    main()