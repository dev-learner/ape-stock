# scripts/bme_full_data.py
# NAME: Dump BME.L Full Data
# DESC: Prints every technical and fundamental field currently held for BME.L.
# DETAIL: Dumps the complete latest row from index_quotes, fundamentals, the most recent daily close, the latest rank, watchlist status, and any open holdings for the symbol BME.L. Created as a reference for the data shape used by a single-stock Grok-It! prompt. Read-only; makes no changes to the database.
# ALLOW_DELETE: 1
# RUN: Tool2
# CATEGORY: uncategorised

"""
Dump BME.L Full Data
--------------------
A read-only diagnostic script that prints every field currently stored
for the symbol BME.L across the main tables:

- index_quotes     (price, change, screener metrics, etc.)
- fundamentals     (valuation, margins, market cap, etc.)
- daily_closes     (most recent bar)
- daily_ranks      (most recent rank)
- watchlist
- holdings         (open positions only)

Useful as a template when building Grok-It! prompts or when debugging
why a particular name looks the way it does in the tools.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "ape_stock.db"
SYMBOL = "BME.L"

def main():
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    print(f"=== Latest data for {SYMBOL} ===\n")

    # --- index_quotes ---
    print("--- index_quotes ---")
    cur.execute("SELECT * FROM index_quotes WHERE symbol = ?", (SYMBOL,))
    row = cur.fetchone()
    if row:
        for key in row.keys():
            print(f"  {key} = {row[key]}")
    else:
        print("  (no row)")
    print()

    # --- fundamentals ---
    print("--- fundamentals ---")
    cur.execute("SELECT * FROM fundamentals WHERE symbol = ?", (SYMBOL,))
    row = cur.fetchone()
    if row:
        for key in row.keys():
            print(f"  {key} = {row[key]}")
    else:
        print("  (no row)")
    print()

    # --- latest daily close ---
    print("--- latest daily_closes ---")
    cur.execute("""
        SELECT date, close, volume
        FROM daily_closes
        WHERE symbol = ?
        ORDER BY date DESC
        LIMIT 1
    """, (SYMBOL,))
    row = cur.fetchone()
    if row:
        print(f"  date = {row['date']}")
        print(f"  close = {row['close']}")
        print(f"  volume = {row['volume']}")
    else:
        print("  (no daily closes)")
    print()

    # --- latest rank ---
    print("--- latest daily_ranks ---")
    cur.execute("""
        SELECT date, rank, score, persistence_days
        FROM daily_ranks
        WHERE symbol = ?
        ORDER BY date DESC
        LIMIT 1
    """, (SYMBOL,))
    row = cur.fetchone()
    if row:
        for key in row.keys():
            print(f"  {key} = {row[key]}")
    else:
        print("  (no rank data)")
    print()

    # --- watchlist ---
    print("--- watchlist ---")
    cur.execute("SELECT * FROM watchlist WHERE symbol = ?", (SYMBOL,))
    row = cur.fetchone()
    if row:
        for key in row.keys():
            print(f"  {key} = {row[key]}")
    else:
        print("  (not on watchlist)")
    print()

    # --- open holdings ---
    print("--- open holdings ---")
    cur.execute("""
        SELECT * FROM holdings
        WHERE symbol = ? AND status = 'open'
    """, (SYMBOL,))
    rows = cur.fetchall()
    if rows:
        for i, h in enumerate(rows, 1):
            print(f"  Holding {i}:")
            for key in h.keys():
                print(f"    {key} = {h[key]}")
    else:
        print("  (no open holdings)")

    conn.close()
    print("\n=== Done ===")

if __name__ == "__main__":
    main()