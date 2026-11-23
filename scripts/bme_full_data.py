# scripts/bme_full_data.py
# DESC: Dump all latest technical and fundamental data for BME.L
# RUN: Tool2

import sqlite3
from pathlib import Path

# Database lives in the project root
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

    # --- index_quotes (price + screener metrics) ---
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

    # --- current rank (most recent) ---
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

    # --- watchlist status ---
    print("--- watchlist ---")
    cur.execute("SELECT * FROM watchlist WHERE symbol = ?", (SYMBOL,))
    row = cur.fetchone()
    if row:
        for key in row.keys():
            print(f"  {key} = {row[key]}")
    else:
        print("  (not on watchlist)")
    print()

    # --- open holdings (if any) ---
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