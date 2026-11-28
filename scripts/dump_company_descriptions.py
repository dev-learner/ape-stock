# scripts/dump_company_descriptions.py
# NAME: Dump Company Descriptions
# DESC: Prints the contents of the company_descriptions table.
# DETAIL: Read-only. Shows symbol, description (truncated) and updated_at for every row.
# ALLOW_DELETE: 1
# RUN: Tool2
# CATEGORY: dumps

"""
Dump Company Descriptions
-------------------------
Simple read-only dump of the company_descriptions table.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "ape_stock.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT symbol, description, updated_at
        FROM company_descriptions
        ORDER BY symbol
    """)
    rows = cur.fetchall()
    conn.close()

    print(f"Company descriptions ({len(rows)} rows)\n")
    print(f"{'Symbol':<10} {'Updated':<20} Description")
    print("-" * 100)

    for r in rows:
        desc = (r["description"] or "").replace("\n", " ")
        if len(desc) > 70:
            desc = desc[:67] + "..."
        updated = r["updated_at"] or ""
        print(f"{r['symbol']:<10} {updated:<20} {desc}")

    print(f"\nTotal: {len(rows)}")

if __name__ == "__main__":
    main()