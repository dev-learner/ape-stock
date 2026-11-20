# scripts/load_external_constituents.py
# DESC: Load Nasdaq, Dow and AIM constituents into external_constituents
# RUN: Tool2

import sqlite3
import time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import yfinance as yf
import warnings
warnings.filterwarnings("ignore")

db_path = Path(__file__).parent.parent / "ape_stock.db"
UK = ZoneInfo("Europe/London")

conn = sqlite3.connect(db_path, timeout=60)
cur = conn.cursor()

today = datetime.now(UK).isoformat()

# ---------- Nasdaq ----------
print("Fetching Nasdaq constituents...")
try:
    nasdaq = yf.Ticker("^IXIC")  # fallback approach
    # Yahoo does not expose a clean constituents endpoint; use a known list source or scrape
    # For reliability we use a small set of major names + note that a full list
    # is better obtained from Nasdaq’s own site or a static file.
    # Here we demonstrate with a few examples; expand as needed.
    nasdaq_symbols = [
        "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO",
        "COST", "NFLX", "AMD", "PEP", "CSCO", "ADBE", "TMUS", "INTC",
        "CMCSA", "QCOM", "TXN", "AMAT", "INTU", "AMGN", "HON", "BKNG",
        "SPCX", "GLND"  # include the ones you care about
    ]
    for sym in nasdaq_symbols:
        try:
            info = yf.Ticker(sym).info
            name = info.get("shortName") or info.get("longName") or sym
            cur.execute("""
                INSERT OR REPLACE INTO external_constituents (symbol, name, market, updated)
                VALUES (?, ?, 'NASDAQ', ?)
            """, (sym, name, today))
        except Exception as e:
            print(f"  {sym}: {e}")
        time.sleep(0.2)
    print(f"  Nasdaq: {len(nasdaq_symbols)} symbols")
except Exception as e:
    print("Nasdaq fetch failed:", e)

# ---------- Dow ----------
print("Fetching Dow constituents...")
try:
    dow = yf.Ticker("^DJI")
    # Dow is small; hard-code the current 30 (update occasionally)
    dow_symbols = [
        "AAPL", "AMGN", "AMZN", "AXP", "BA", "CAT", "CRM", "CSCO", "CVX",
        "DIS", "GS", "HD", "HON", "IBM", "JNJ", "JPM", "KO", "MCD", "MMM",
        "MRK", "MSFT", "NKE", "NVDA", "PG", "TRV", "UNH", "V", "VZ", "WMT", "GOOGL"
    ]
    for sym in dow_symbols:
        try:
            info = yf.Ticker(sym).info
            name = info.get("shortName") or info.get("longName") or sym
            cur.execute("""
                INSERT OR REPLACE INTO external_constituents (symbol, name, market, updated)
                VALUES (?, ?, 'DOW', ?)
            """, (sym, name, today))
        except Exception as e:
            print(f"  {sym}: {e}")
        time.sleep(0.2)
    print(f"  Dow: {len(dow_symbols)} symbols")
except Exception as e:
    print("Dow fetch failed:", e)

# ---------- AIM ----------
print("Fetching AIM constituents...")
try:
    # AIM list is not directly available via yfinance.
    # Placeholder: add a few known AIM names or leave empty for manual addition.
    aim_symbols = [
        "TLW.L",  # Tullow Oil (AIM / smaller)
        # add more as needed
    ]
    for sym in aim_symbols:
        try:
            info = yf.Ticker(sym).info
            name = info.get("shortName") or info.get("longName") or sym
            cur.execute("""
                INSERT OR REPLACE INTO external_constituents (symbol, name, market, updated)
                VALUES (?, ?, 'AIM', ?)
            """, (sym, name, today))
        except Exception as e:
            print(f"  {sym}: {e}")
        time.sleep(0.2)
    print(f"  AIM: {len(aim_symbols)} symbols")
except Exception as e:
    print("AIM fetch failed:", e)

conn.commit()
conn.close()
print("Done.")