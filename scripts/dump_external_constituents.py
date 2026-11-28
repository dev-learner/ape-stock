# scripts/dump_external_constituents.py
# NAME: Dump External Constituents
# DESC: Prints every row from the external_constituents table.
# DETAIL: Diagnostic dump of any non-FTSE symbols that have been loaded. Read-only.
# ALLOW_DELETE: 1
# RUN: Tool2
# CATEGORY: dumps

"""
Dump External Constituents
--------------------------
Prints the contents of the external_constituents table (Nasdaq, Dow, AIM, etc.).
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "ape_stock.db"

def main():
    conn = sqlite3.connect(DB_PATH)
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

if __name__ == "__main__":
    main()