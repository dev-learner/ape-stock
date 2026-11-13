# scripts/update_fundamentals.py
# DESC: Fill sector, industry, market cap, PE, yields, dates and other fundamentals
# RUN: VENV

"""
Fill sector, industry, market_cap, avg_volume, PE, dividend yield,
shares outstanding, 52-week high/low, beta, book value, P/B,
ex-dividend date and earnings date.
"""
import sqlite3
import time
from pathlib import Path
from datetime import datetime, timezone
import yfinance as yf
import warnings
warnings.filterwarnings("ignore")

db_path = Path(__file__).parent.parent / "ape_stock.db"
conn = sqlite3.connect(db_path, timeout=30)
cur = conn.cursor()

columns = [
    ("sector", "TEXT"),
    ("industry", "TEXT"),
    ("market_cap", "INTEGER"),
    ("avg_volume", "INTEGER"),
    ("pe_trailing", "REAL"),
    ("pe_forward", "REAL"),
    ("dividend_yield", "REAL"),
    ("shares_outstanding", "INTEGER"),
    ("fifty_two_week_high", "REAL"),
    ("fifty_two_week_low", "REAL"),
    ("beta", "REAL"),
    ("book_value", "REAL"),
    ("price_to_book", "REAL"),
    ("ex_dividend_date", "TEXT"),
    ("earnings_date", "TEXT"),
]

for col, typ in columns:
    try:
        cur.execute(f"ALTER TABLE index_quotes ADD COLUMN {col} {typ}")
        print(f"Added column: {col}")
    except sqlite3.OperationalError:
        pass
conn.commit()

def ts_to_date(ts):
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d")
    except Exception:
        return None

cur.execute("SELECT symbol FROM index_quotes")
symbols = [r[0] for r in cur.fetchall()]
print(f"Updating fundamentals for {len(symbols)} symbols…")

updated = 0
for i, sym in enumerate(symbols, 1):
    try:
        info = yf.Ticker(sym).info or {}

        data = {
            "sector": info.get("sector") or info.get("sectorDisp"),
            "industry": info.get("industry") or info.get("industryDisp"),
            "market_cap": info.get("marketCap"),
            "avg_volume": info.get("averageDailyVolume3Month") or info.get("averageDailyVolume10Day"),
            "pe_trailing": info.get("trailingPE"),
            "pe_forward": info.get("forwardPE"),
            "dividend_yield": info.get("dividendYield"),
            "shares_outstanding": info.get("sharesOutstanding"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "beta": info.get("beta"),
            "book_value": info.get("bookValue"),
            "price_to_book": info.get("priceToBook"),
            "ex_dividend_date": ts_to_date(info.get("exDividendDate")),
            "earnings_date": ts_to_date(info.get("earningsTimestamp") or info.get("earningsTimestampStart")),
        }

        set_clause = ", ".join(f"{k} = COALESCE(?, {k})" for k in data)
        values = list(data.values()) + [sym]

        cur.execute(f"""
            UPDATE index_quotes
            SET {set_clause}
            WHERE symbol = ?
        """, values)

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