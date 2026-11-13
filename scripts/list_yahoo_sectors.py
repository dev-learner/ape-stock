# scripts/list_yahoo_sectors.py
# DESC: List all Yahoo Finance sectors and their industries
# RUN: Tool2

import sqlite3
from pathlib import Path
from collections import Counter
import yfinance as yf

db_path = Path(__file__).parent.parent / "ape_stock.db"
conn = sqlite3.connect(db_path, timeout=30)
cur = conn.cursor()

cur.execute("SELECT DISTINCT symbol FROM index_constituents ORDER BY symbol")
symbols = [r[0] for r in cur.fetchall()]
conn.close()

print(f"Fetching sector/industry for {len(symbols)} symbols…\n")

sectors = Counter()
industries = Counter()
details = []

for i, sym in enumerate(symbols, 1):
    try:
        info = yf.Ticker(sym).info
        sector = info.get("sector") or "—"
        industry = info.get("industry") or "—"
        sectors[sector] += 1
        industries[industry] += 1
        details.append((sym, sector, industry))
        if i % 50 == 0:
            print(f"  …{i}/{len(symbols)}", flush=True)
    except Exception as e:
        print(f"  {sym}: {e}")

print("\n=== SECTORS ===")
for name, count in sectors.most_common():
    print(f"{count:4}  {name}")

print("\n=== INDUSTRIES ===")
for name, count in industries.most_common():
    print(f"{count:4}  {name}")

print(f"\nTotal symbols processed: {len(details)}")