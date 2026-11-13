# scripts/update_sectors.py
# DESC: Early version – fill sector and industry only
# RUN: VENV

"""
Add sector & industry to index_quotes for all FTSE constituents.
"""
import sqlite3
import time
from pathlib import Path
import yfinance as yf
import warnings
warnings.filterwarnings("ignore", category=Warning)

db_path = Path(__file__).parent.parent / "ape_stock.db"
conn = sqlite3.connect(db_path, timeout=30)
cur = conn.cursor()

# Add columns if they don't exist
for col in ("sector", "industry"):
    try:
        cur.execute(f"ALTER TABLE index_quotes ADD COLUMN {col} TEXT")
        print(f"Added column: {col}")
    except sqlite3.OperationalError:
        pass  # already exists
conn.commit()

# Get all symbols
cur.execute("SELECT DISTINCT symbol FROM index_constituents")
symbols = [r[0] for r in cur.fetchall()]
print(f"Updating sector/industry for {len(symbols)} symbols…")

updated = 0
for i, sym in enumerate(symbols, 1):
    try:
        info = yf.Ticker(sym).info
        sector = info.get("sector") or info.get("sectorDisp")
        industry = info.get("industry") or info.get("industryDisp")
        if sector or industry:
            cur.execute("""
                UPDATE index_quotes
                SET sector = ?, industry = ?
                WHERE symbol = ?
            """, (sector, industry, sym))
            if cur.rowcount:
                updated += 1
        if i % 25 == 0:
            print(f"  …{i}/{len(symbols)}", flush=True)
            conn.commit()
        time.sleep(0.25)
    except Exception as e:
        print(f"  {sym}: {e}")

conn.commit()
conn.close()
print(f"Done. Updated {updated} symbols.")