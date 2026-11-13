# scripts/add_market_cap.py
# DESC: Add and populate market_cap column
# RUN: VENV

import sqlite3
import time
from pathlib import Path
import yfinance as yf
import warnings
warnings.filterwarnings("ignore")

db_path = Path(__file__).parent.parent / "ape_stock.db"
conn = sqlite3.connect(db_path, timeout=30)
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE index_quotes ADD COLUMN market_cap INTEGER")
    print("Added market_cap column")
except sqlite3.OperationalError:
    print("market_cap column already exists")
conn.commit()

cur.execute("SELECT symbol FROM index_quotes")
symbols = [r[0] for r in cur.fetchall()]
print(f"Filling market_cap for {len(symbols)} symbols…")

updated = 0
for i, sym in enumerate(symbols, 1):
    try:
        info = yf.Ticker(sym).info
        mkt = info.get("marketCap")
        if mkt:
            cur.execute("UPDATE index_quotes SET market_cap = ? WHERE symbol = ?", (mkt, sym))
            updated += 1
        if i % 25 == 0:
            print(f"  …{i}/{len(symbols)}", flush=True)
            conn.commit()
        time.sleep(0.2)
    except Exception as e:
        print(f"  {sym}: {e}")

conn.commit()
conn.close()
print(f"Done. Updated {updated} symbols.")