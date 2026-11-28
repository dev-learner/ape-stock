# scripts/fetch_company_descriptions.py
# NAME: Fetch Company Descriptions
# DESC: Fetches a short business description for every FTSE 100 & FTSE 250 constituent and stores it in company_descriptions.
# DETAIL: Uses yfinance longBusinessSummary (trimmed to ~2–3 sentences). Creates the table if needed. Safe to re-run (INSERT OR REPLACE). Only processes symbols already present in index_quotes. Read-only on market data.
# ALLOW_DELETE: 1
# RUN: Tool2
# CATEGORY: data

"""
Fetch Company Descriptions
--------------------------
Populates the company_descriptions table for all symbols currently in index_quotes.
"""

import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
import yfinance as yf

DB_PATH = Path(__file__).parent.parent / "ape_stock.db"
SLEEP_SECONDS = 0.4

def get_ftse_symbols(conn):
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT symbol FROM index_quotes WHERE symbol IS NOT NULL")
    return [row[0] for row in cur.fetchall()]

def fetch_description(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}
        summary = info.get("longBusinessSummary") or info.get("shortBusinessSummary")
        if summary and len(summary.strip()) > 40:
            text = summary.strip().replace("\n", " ")
            sentences = text.split(". ")
            short = ". ".join(sentences[:3]).strip()
            if not short.endswith("."):
                short += "."
            return short
    except Exception:
        pass
    return None

def main():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS company_descriptions (
            symbol TEXT PRIMARY KEY,
            description TEXT,
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)

    symbols = get_ftse_symbols(conn)
    print(f"Found {len(symbols)} symbols in index_quotes\n")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    updated = 0
    missing = 0

    for i, sym in enumerate(symbols, 1):
        print(f"[{i}/{len(symbols)}] {sym} ... ", end="", flush=True)
        desc = fetch_description(sym)
        if desc:
            cur.execute("""
                INSERT OR REPLACE INTO company_descriptions (symbol, description, updated_at)
                VALUES (?, ?, ?)
            """, (sym, desc, now))
            updated += 1
            print("OK")
        else:
            missing += 1
            print("no description")
        time.sleep(SLEEP_SECONDS)

    conn.commit()
    conn.close()
    print(f"\nDone. Updated: {updated}   Missing: {missing}")

if __name__ == "__main__":
    main()