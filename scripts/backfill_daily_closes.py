# scripts/backfill_daily_closes.py
# DESC: Back-fill 1 year of daily OHLCV into daily_closes
# RUN: VENV

import sqlite3
import time
import warnings
from pathlib import Path
import yfinance as yf

warnings.filterwarnings("ignore", category=Warning)

db_path = Path(__file__).parent.parent / "ape_stock.db"
conn = sqlite3.connect(db_path, timeout=30)
cur = conn.cursor()

for col, typ in [("open", "REAL"), ("high", "REAL"), ("low", "REAL")]:
    try:
        cur.execute(f"ALTER TABLE daily_closes ADD COLUMN {col} {typ}")
        print(f"Added {col} column")
    except sqlite3.OperationalError:
        pass
conn.commit()

cur.execute("SELECT symbol FROM index_constituents")
symbols = [r[0] for r in cur.fetchall()]
print(f"Back-filling {len(symbols)} symbols – 1 year (OHLCV)…")

inserted = 0
for i, sym in enumerate(symbols, 1):
    try:
        hist = yf.Ticker(sym).history(period="1y", interval="1d", auto_adjust=False)
        if hist.empty:
            continue
        for dt, row in hist.iterrows():
            date_str = dt.strftime("%Y-%m-%d")
            o = float(row["Open"]) if row["Open"] == row["Open"] else None
            h = float(row["High"]) if row["High"] == row["High"] else None
            l = float(row["Low"]) if row["Low"] == row["Low"] else None
            c = float(row["Close"]) if row["Close"] == row["Close"] else None
            v = int(row["Volume"]) if row["Volume"] == row["Volume"] else None
            if c is None:
                continue
            cur.execute("""
                INSERT OR REPLACE INTO daily_closes
                (symbol, date, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (sym, date_str, o, h, l, c, v))
            inserted += 1
        if i % 25 == 0:
            print(f"  …{i}/{len(symbols)}", flush=True)
            conn.commit()
        time.sleep(0.3)
    except Exception as e:
        print(f"  {sym}: {e}")

conn.commit()
conn.close()
print(f"Done. Upserted {inserted} rows.")